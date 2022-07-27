"""Utility functions for working with STAC items."""
import os
from dataclasses import dataclass, field
from typing import Dict, Iterator, List
from urllib.parse import urlparse

import pystac
import requests
from loguru import logger

from metaearth.util.misc import stream_download

from ..provider import BaseProvider


@dataclass
class ExtractAsset:
    """ExtractAsset represents an asset be extracted from a STAC item."""

    id: str = field()
    asset_name: str = field()
    dtype: str = field()
    asset: pystac.Asset = field()
    provider: BaseProvider = field()
    outfile: str = field()
    filesize_mb: int = field(default=-1)
    download_attempts: int = field(default=0)
    _last_download_url: str = field(default="")

    def query_asset_size_from_download_url(self) -> int:
        """Query the size of the asset from the download url using an http request."""
        download_url = self.provider.asset_to_download_url(self.asset)
        with requests.get(download_url, stream=True, timeout=10) as response:
            response.raise_for_status()
            if response.headers.get("Content-Length"):
                clen: str = response.headers.get("Content-Length", "")
                self.filesize_mb = int(clen) // 1024 // 1024
            else:
                self.filesize_mb = -1
        return self.filesize_mb

    def download(self) -> None:
        """Download the asset from the provider."""
        self.download_attempts += 1
        download_url = self.provider.asset_to_download_url(self.asset)
        # keep track of the last download url for error reporting
        self._last_download_url = download_url
        logger.debug(f"Downloading {download_url} to {self.outfile}")
        stream_download(download_url, self.outfile)
        logger.debug(f"Downloaded {self.outfile}")

    def filesize_unknown(self) -> bool:
        """Return True if the filesize is unknown."""
        return self.filesize_mb <= 0


@dataclass
class ExtractAssetCollection:
    """A collection of assets to be extracted from a collection of ExtractAsset objects.

    Each asset is stored in a list associated with the higher-level STAC item.
    Iterating over ExtractAssetCollection will iterate over the assets in the collection.
    ExtractAssetCollection.assets provides a dictionary of lists of assets associated
    with each item in the collection.
    """

    assets: Dict[str, List[ExtractAsset]] = field(default_factory=dict)

    def __iter__(self) -> Iterator[ExtractAsset]:
        """Iterate over the assets in the collection."""
        for asset_list in self.assets.values():
            yield from asset_list

    def __len__(self) -> int:
        """Return the number of assets in the collection."""
        return len(self.assets)

    def __add__(self, other: "ExtractAssetCollection") -> "ExtractAssetCollection":
        """Add two ExtractAssetCollections together."""
        for id, asts in other.assets.items():
            if id not in self.assets:
                self.assets[id] = []
            self.assets[id].extend(asts)
        return self

    def number_of_assets_with_unknown_size(self) -> int:
        """Return the number of assets with unknown size."""
        return sum(1 for asset in self if asset.filesize_mb <= 0)

    def total_size(self) -> int:
        """Return the total size (in MB) of all assets in the collection."""
        return sum(asset.filesize_mb for asset in self)

    def summary(self) -> None:
        """Print a summary of the collection."""
        assets_types: Dict[str, str] = {}
        for ast in self:
            assets_types[ast.asset_name] = ast.asset.description
            logger.debug(f"\n{ast.id} ({ast.dtype}): {ast.filesize_mb} MB")
        ast_type_str = "\n" + "\n".join(
            [f'key={k}; desc="{v}"' for k, v in assets_types.items()]
        )
        logger.info(f"Asset types: {ast_type_str}")
        logger.info(f"Total asset size: {self.total_size():,} MB")
        if self.number_of_assets_with_unknown_size() > 0:
            logger.info(
                f"Number of assets with unknown size: {self.number_of_assets_with_unknown_size()}"
            )

    def add_asset(self, asset: ExtractAsset) -> None:
        """Add an asset to the collection."""
        if asset.id not in self.assets:
            self.assets[asset.id] = []
        self.assets[asset.id].append(asset)


def extract_assets_from_item(
    itm: pystac.Item, pvdr: BaseProvider, itm_assets_to_extract: List[str], outdir: str
) -> ExtractAssetCollection:
    """Build an ExtractAssetCollection object from a single STAC item.

    Args:
        itm (pystac.Item): The item to extract assets from.
        pvdr (BaseProvider): The provider for the item.
        itm_assets_to_extract (List[str]): A list of asset types to extract.
        outdir (str): The output directory.
    """
    assets = itm.get_assets()
    if len(itm_assets_to_extract) == 1 and itm_assets_to_extract[0] == "all":
        itm_assets_to_extract = assets.keys()

    extract_assets = ExtractAssetCollection()
    for asset_name in itm_assets_to_extract:
        if asset_name not in assets:
            logger.warning(f"{itm.id} has no asset {asset_name}")
            continue
        asset = assets[asset_name]
        outfile = item_asset_to_outfile(itm, asset, outdir)

        adct = asset.to_dict()
        file_size = adct.get("file:size", "???")

        try:
            file_size = round(int(file_size) / 1e6)
        except ValueError:
            file_size = -1
        file_type = adct.get("type", "???")
        ea = ExtractAsset(
            f"{itm.id}_{asset_name}",
            asset_name,
            file_type,
            asset,
            pvdr,
            outfile,
            file_size,
        )
        extract_assets.add_asset(ea)

    return extract_assets


def item_asset_to_outfile(itm: pystac.Item, asset: pystac.Asset, outdir: str) -> str:
    """Take an item and returns the output filename for it.

    Args:
        itm (pystac.Item): The item to get the output filename for
        asset (pystac.Asset): The asset associated with the item
        outdir (str): The output directory
    Returns:
        str: The output filename
    """
    outname = os.path.basename(urlparse(asset.href).path)
    return os.path.join(outdir, itm.collection_id, itm.id, outname)
