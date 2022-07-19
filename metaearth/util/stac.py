import asyncio
from dataclasses import dataclass, field
import os
from typing import Dict, List
from urllib.parse import urlparse

import httpx
import pystac
from loguru import logger
from ..provider import BaseProvider
from .misc import stream_download_file

@dataclass
class ExtractAsset:
    """ ExtractAsset represents a single asset that is to be 
    extracted from a STAC item.
    """
    id: str = field()
    dtype: str = field()
    asset: pystac.Asset = field()
    provider: BaseProvider = field()
    outfile: str = field()
    filesize_mb: int = field(default=-1)

    async def set_asset_size_from_download_url(self, download_url: str) -> None:
        client = httpx.AsyncClient()
        async with client.stream("GET", download_url, timeout=60) as response:
            total = int(response.headers["Content-Length"])
            self.filesize_mb = total//1000000
    
    def filesize_unknown(self) -> bool:
        """ Returns True if the filesize is unknown. """
        return self.filesize_mb < 0

@dataclass
class ExtractAssetCollection:
    """ ExtractAssetCollection represents a collection of assets that are to be
    extracted from a collection of ExtractAsset objects.
    """
    assets: Dict[str, List[ExtractAsset]] = field(default_factory=dict)

    def __iter__(self):
        """ Iterate over the assets in the collection. """
        for asset_id in self.assets:
            yield self.assets[asset_id][0]

    def __len__(self):
        """ Return the number of assets in the collection. """
        return len(self.assets)
    
    def __add__(self, other: 'ExtractAssetCollection'):
        """ Add two ExtractAssetCollections together. """
        for id, asts in other.assets.items():
            if id not in self.assets:
                self.assets[id] = []
            self.assets[id].extend(asts)
        return self
    
    def number_of_assets_wtih_unknown_size(self):
        return sum([len(a) for a in self.assets.values() if a[0].filesize_mb < 0])

    def total_size(self):
        return sum([a[0].filesize_mb for a in self.assets.values() if a[0].filesize_mb > 0])
    
    def summary(self):
        """ Print a summary of the collection. """
        for id, asts in self.assets.items():
            pvdrs = '\n\t\t'.join([str(a.provider) for a in asts])
            logger.debug(f"\n{id} ({asts[0].dtype}): {asts[0].filesize_mb} MB\n\t{len(asts)} provider{'s' if len(asts) > 1 else ''}:\n\t\t{pvdrs}")
        logger.info(f"Total asset size: {self.total_size():,} MB")
        if self.number_of_assets_wtih_unknown_size() > 0:
            logger.info(f"Number of assets with unknown size: {self.number_of_assets_wtih_unknown_size()}")
    
    def add_asset(self, asset: ExtractAsset):
        """ Add an asset to the collection. """
        if asset.id not in self.assets:
            self.assets[asset.id] = []
        self.assets[asset.id].append(asset)

def extract_assets_from_item(itm: pystac.Item, pvdr: BaseProvider, itm_assets_to_extract: List[str], outdir: str) -> ExtractAssetCollection:
    """ Build an ExtractAssetCollection object from a single STAC item. """

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
        if "file:size" in adct:
            file_size = adct.get("file:size", "???")
            
        try:
            file_size = round(int(file_size)/1e6)
        except:
            file_size = -1
        file_type = adct.get("type", "???")
        ea = ExtractAsset(f"{itm.id}_{asset_name}", file_type, asset, 
                                        pvdr, outfile, file_size)
        extract_assets.add_asset(ea)
    
    return extract_assets

async def extract_asset(ast: ExtractAsset) -> asyncio.coroutine:
    """This async downloads the assets to the outfile

    Args:
    ExtractAsset: The asset to extract
    """
    # it's possible another extraction task already downloaded this task
    if os.path.exists(ast.outfile):
        logger.debug(f"Skipping {ast.outfile}, exists")
        return
    
    download_url = ast.provider.asset_to_download_url(ast.asset)
    
    logger.debug(f"Downloading {download_url} to {ast.outfile}")
    if os.path.exists(ast.outfile):
        logger.debug(f"Skipping {ast.outfile}, exists")
        return
    
    await stream_download_file(download_url, ast.outfile)
            
def item_asset_to_outfile(itm: pystac.Item, asset: pystac.Asset, outdir: str) -> str:
    """This takes an item and returns the output filename for it

    Args:
        item (pystac.Item): The item to get the output filename for
        asset (pystac.Asset): The asset associated with the item
        outdir (str): The output directory
    Returns:
        str: The output filename
    """
    outname = os.path.basename(urlparse(asset.href).path)
    return os.path.join(outdir, itm.collection_id, itm.id, outname)
