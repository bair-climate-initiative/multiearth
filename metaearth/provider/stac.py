"""A Generic STAC Provider."""

import os
from queue import Empty
from time import sleep
from typing import Any, Callable, Iterator, List, Union

import geopandas as gpd
import pystac
import requests
import shapely
import shapely.geometry
from loguru import logger
from pystac_client import Client
from tqdm import tqdm
from tqdm.contrib.concurrent import thread_map

from ..assets import DownloadWrapper, ExtractAsset, ExtractAssetCollection
from ..config import CollectionSchema, ConfigSchema, ProviderKey
from ..util.misc import item_href_to_outfile, stream_download
from ..util.multi import create_download_workers_and_queues
from .base import BaseProvider

__all__ = ["STACProvider"]


class STACProvider(BaseProvider):
    """Provides standard STAC API region_to_items method."""

    description: str = "STAC Provider"

    # max items allowed client
    _max_items: int = 10000
    _default_client_url: str
    _client: Client
    completed_assets: ExtractAssetCollection
    error_assets: ExtractAssetCollection
    all_assets: ExtractAssetCollection

    def __init__(
        self,
        id: ProviderKey,
        cfg: ConfigSchema,
        collections: List[CollectionSchema],
        client_url: str = "",
        **kwargs: Any,
    ) -> None:
        """Set up the STAC Provider.

        It's intended that this method will be overridden by subclasses and call super().__init__().
        """
        super().__init__(id, cfg, collections)

        if client_url == "":
            if self._default_client_url == "":
                raise ValueError(f"Client URL not provided for {self}.")
            client_url = self._default_client_url
        self._client = Client.open(client_url, ignore_conformance=True)

        self.completed_assets = ExtractAssetCollection()
        self.error_assets = ExtractAssetCollection()

    # abstractclassmethod
    def check_authorization(self) -> bool:
        """Check if the provider is authorized - meant to be overridden."""
        return True

    # abstractclassmethod
    def extract_assets(self, dry_run: bool = False) -> bool:
        """Extract assets from the collections in the configuration.

        Returns: True if all assets extracted successfully, False otherwise.
        """
        # This method operates as follows:
        # 1. For each collection in the configuration, query the items in the collection
        # 2. For each item in the collection, query the assets in the
        #    item and obtain filesizes if possible
        # 3. Add all assets to the extraction queue
        # 4. Download each asset in the extraction queue

        self.all_assets = ExtractAssetCollection()
        for coll_cfg in self.collections:
            ea_coll = self._get_extract_assets_collection(coll_cfg)
            self.all_assets += ea_coll

        self._prepare_assets_for_extraction(self.all_assets)
        summary, detailed = self.all_assets.summary()
        logger.info("\n\n" + summary)
        logger.debug(detailed)

        # kick off the download if not a dry run
        success = True
        if not dry_run:
            success = self._download()
        else:
            logger.info("Dry run - not downloading assets.")
        return success

    def _get_extract_assets_collection(
        self, cfg: CollectionSchema
    ) -> ExtractAssetCollection:
        """Get the collection for the extract assets."""
        # read/parse aoi if needed
        aoi = None
        if cfg.aoi_file:
            logger.debug(f"loading area of interest file: {cfg.aoi_file}")
            aoi = gpd.read_file(cfg.aoi_file).unary_union

        # appease mypy
        dt = cfg.datetime if cfg.datetime else ""
        id = cfg.id if cfg.id else ""
        outdir = cfg.outdir if cfg.outdir else ""
        assets = cfg.assets if cfg.assets else []

        # get the items from the input cfg
        itm_set = list(self._region_to_items(aoi, dt, id, cfg.max_items))
        logger.info(
            f"{self} returned {len(itm_set)} items for {id} "
            + f"for datetime {cfg.datetime}"
        )

        logger.debug(f"Adding item assets from {self} to extraction tasks")
        outdir = os.path.join(outdir, id)
        extract_assets = ExtractAssetCollection()
        for itm in itm_set:
            extract_assets += self._extract_assets_from_item(itm, assets, outdir)

        return extract_assets

    def _region_to_items(
        self,
        region: Union[shapely.geometry.Polygon, shapely.geometry.MultiPolygon],
        datetime: str,
        collection: str,
        max_items: int,
    ) -> Iterator[pystac.Item]:
        """Create ItemCollection from a given region between start_date and end_date.

        Args:
            region (Union[shapely.geometry.Polygon, shapely.geometry.MultiPolygon]): the region
            datetime (str): Single date+time, or a range ('/' separator), formatted to RFC 3339,
                section 5.6. Use double dots .. for open date ranges.
            collection (str): collection to include in the returned ItemCollection
            max_items (int): maximum number of items to return, -1 for no limit/provider limit
        Returns:
            Iterator[pystac.Item]: an iterable that contains the pystac items
        """
        if max_items < 0:
            max_items = self._max_items
        search = self._client.search(
            datetime=datetime,
            collections=collection,
            intersects=region,
            max_items=max_items,
        )
        items: Iterator[pystac.Item] = search.items()
        return items

    def _extract_assets_from_item(
        self, itm: pystac.Item, itm_assets_to_extract: List[str], outdir: str
    ) -> ExtractAssetCollection:
        """Build an ExtractAssetCollection object from a single STAC item.

        Args:
            itm (pystac.Item): The item to extract assets from.
            pvdr (BaseProvider): The provider for the item.
            itm_assets_to_extract (List[str]): A list of asset types to extract.
            outdir (str): The output directory.
        """
        assert itm.collection_id is not None, "Item must have a collection ID"

        assets = itm.get_assets()
        if len(itm_assets_to_extract) == 1 and itm_assets_to_extract[0] == "all":
            itm_assets_to_extract = list(assets.keys())

        extract_assets = ExtractAssetCollection()
        for asset_name in itm_assets_to_extract:
            if asset_name not in assets:
                logger.warning(f"{itm.id} has no asset {asset_name}")
                continue
            asset = assets[asset_name]
            asset_outdir = os.path.join(outdir, itm.id)
            outfile = item_href_to_outfile(asset.href, asset_outdir)

            adct = asset.to_dict()
            file_size = adct.get("file:size", "???")

            try:
                file_size = round(int(file_size) / 1e6)
            except ValueError:
                file_size = -1
            file_type = adct.get("type", "???")
            ea = ExtractAsset(
                id=f"{itm.id}_{asset_name}",
                asset_name=asset_name,
                dtype=file_type,
                asset=asset,
                outfile=outfile,
                filesize_mb=file_size,
                provider_name=self.description,
                collection_name=itm.collection_id,
            )
            extract_assets.add_asset(ea)

        return extract_assets

    def _prepare_assets_for_extraction(
        self, extract_assets: ExtractAssetCollection
    ) -> None:
        """Prepare assets for extraction.

        For STAC collections, this means checking the filesize of the assets
        and then using the filesize of the assets to determine if they're already
        downloaded.

        Args:
            extract_assets (ExtractAssetCollection): The collection of assets to prepare.
        """
        logger.debug("Checking asset sizes")
        asts_with_unknown_filesize = []
        for ast in extract_assets:
            if ast.filesize_unknown():
                asts_with_unknown_filesize.append(ast)

        if len(asts_with_unknown_filesize) > 0:
            if self.cfg.system.query_asset_sizes:
                logger.info(
                    f"{len(asts_with_unknown_filesize):,} assets did not specify file size, "
                    + "will query size directly with http request (this may take a few moments)\n"
                    + "system.query_asset_sizes=False can be used to disable this behavior"
                )

                thread_map(
                    lambda ast: self._query_asset_size_from_download_url(ast),
                    asts_with_unknown_filesize,
                    max_workers=self.cfg.system.max_concurrent_extractions,
                )

        assets_with_unknown_filesize = sum(
            1 for ast in extract_assets if ast.filesize_unknown()
        )
        if assets_with_unknown_filesize > 0:
            logger.info(f"{assets_with_unknown_filesize} assets have unknown file size")

        # Remove possibly corrupt downloads
        removed_ct = 0
        for ast in extract_assets:
            if os.path.exists(ast.outfile):
                # check if the size of the file is as expected, else remove
                skip = True
                mb_size = os.path.getsize(ast.outfile) // 1e6
                if ast.filesize_mb > 0 and max(5, abs(mb_size - ast.filesize_mb)) > 5:
                    if self.cfg.system.remove_existing_if_wrong_size:
                        logger.info(
                            f"Removing {ast.outfile} because it is {mb_size:,}MB"
                            + f" instead of {ast.filesize_mb:,}MB"
                        )
                        os.remove(ast.outfile)
                        ast.downloaded = False
                        skip = False
                    else:
                        logger.info(
                            "The following file is the wrong size, "
                            + "but cfg.system.remove_existing_if_wrong_size"
                            + f" is not set to true, so will not remove: {ast.outfile}"
                        )
                if skip:
                    logger.debug(f"Skipping {ast.outfile}, exists")
                    ast.downloaded = True
                    continue

        if removed_ct > 0:
            logger.info(
                f"Removed {removed_ct:,} files that may not be fully downloaded or corrupt"
            )

    def _query_asset_size_from_download_url(self, asset: ExtractAsset) -> int:
        """Query the size of the asset from the download url using an http request."""
        download_url = self._get_asset_to_download_url_fn()(asset.asset)
        asset.filesize_mb = -1
        with requests.get(download_url, stream=True, timeout=10) as response:
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                logger.warning(f"Error getting size of {download_url}: {e}")
                return -1
            if response.headers.get("Content-Length"):
                clen: str = response.headers.get("Content-Length", "")
                asset.filesize_mb = int(clen) // 1024 // 1024
            else:
                asset.filesize_mb = -1
        return asset.filesize_mb

    def _get_asset_to_download_url_fn(self) -> Callable[[pystac.Asset], str]:
        """Take a single input item and return a download url.

        Args:
            asset (pystac.Asset): a STAC asset
        Returns:
            str: a download url for the given item
        """
        return _asset_to_download_url

    def _download(self) -> bool:
        """Download the assets and return true if no errors."""
        if self.all_assets is None or self.all_assets.num_assets_to_download() == 0:
            return True

        logger.info("Starting data download")

        job_q, finished_q, fail_q = create_download_workers_and_queues(
            self.cfg.system.max_concurrent_extractions,
            self.cfg.system.max_download_attempts,
        )

        for ast in self.all_assets:
            if not ast.downloaded:
                dwrap = DownloadWrapper(
                    asset=ast,
                    download_func=_download_wrapper_fn,
                    download_kwargs=dict(
                        ast=ast,
                        asset_to_download_url=self._get_asset_to_download_url_fn(),
                    ),
                )
                job_q.put(dwrap)

        # show progress bar
        use_num_assets = True
        if self.all_assets.num_assets_with_unknown_size() > 0:
            tqdm_target = self.all_assets.num_assets_to_download()
            tqdm_target_desc = "Assets"
        else:
            use_num_assets = False
            tqdm_target = self.all_assets.total_undownloaded_size()
            tqdm_target_desc = "MB"

        with tqdm(total=tqdm_target, desc=tqdm_target_desc) as pbar:
            while True:
                done_querying = False
                try:
                    completed_ast = finished_q.get(timeout=5).asset
                    completed_ast.downloaded = True
                    self.completed_assets.add_asset(completed_ast)
                    pbar.update(1 if use_num_assets else completed_ast.filesize_mb)
                    done_querying = True
                except Empty:
                    # it's possible all extractions error'd out, and the queue would never return,
                    # so check periodically (after timeout)
                    pass

                # TODO figure out how to do this without relying on internals
                if job_q._unfinished_tasks._semlock._is_zero():  # type: ignore
                    if use_num_assets:
                        pbar.update(self.all_assets.num_assets_to_download() - pbar.n)
                    elif done_querying:
                        pbar.update(self.all_assets.total_undownloaded_size() - pbar.n)
                    break
                sleep(1)

        job_q.join()

        # Log the failed extractions to a file
        error_assets = ExtractAssetCollection()
        if not fail_q.empty():
            fail_file = os.path.join(
                self.cfg.system.log_outdir, f"{self.cfg.run_id}_failed.log"
            )
            with open(fail_file, "w") as f:
                while not fail_q.empty():
                    dwrap, ex = fail_q.get()
                    error_assets.add_asset(dwrap.asset)
                    f.write(f"{dwrap.asset} <{ex}>\n")
            logger.warning(
                f"Failed to download {len(error_assets)} assets: logged failures to {fail_file}"
            )
        fail_q.close()
        return len(self.error_assets) == 0


def _download_wrapper_fn(
    asset_to_download_url: Callable[[pystac.Asset], str], ast: ExtractAsset
) -> None:
    """Asset download wrapper function for multiproc download."""
    url = asset_to_download_url(ast.asset)
    stream_download(url, ast.outfile)


def _asset_to_download_url(asset: pystac.Asset) -> str:
    """Return the download url for the given asset."""
    return str(asset.href)
