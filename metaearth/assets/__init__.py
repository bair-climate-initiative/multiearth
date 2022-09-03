""" Models for asset extraction and management.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List

from loguru import logger

from ..util.misc import stream_download

__all__ = ["ExtractAsset", "ExtractAssetCollection"]


@dataclass
class DownloadWrapper:
    """Wrapper for downloading assets.

    This is a wrapper around the download function for an asset, which is
    responsible for downloading the asset and returning the local path to the
    downloaded asset. This is useful for downloading assets in parallel, as
    the download function is not pickleable and cannot be passed to a
    multiprocessing worker.

    Args:
        download_func (Callable): the download function for the asset
        download_kwargs (Dict): the kwargs for the download function
    """

    download_func: Any
    download_kwargs: Dict = field(default_factory=dict)
    download_attempts: int = field(default=0)
    last_download_url: str = field(default="")
    asset: Any = field(default=None)

    def __call__(self) -> str:
        """Call the download function."""
        return self.download_func(**self.download_kwargs)


@dataclass
class ExtractAsset:
    """ExtractAsset represents an asset be extracted."""

    id: str = field()
    asset_name: str = field()
    dtype: str = field()
    asset: Any = field()
    outfile: str = field()
    downloaded: bool = field(default=False)
    filesize_mb: int = field(default=-1)

    # def download(self, url) -> None:
    #     """Download the asset from the provider."""
    #     # keep track of the last download url for error reporting
    #     self.last_download_url = url
    #     logger.debug(f"Downloading {url} to {self.outfile}")
    #     stream_download(url, self.outfile)
    #     logger.debug(f"Downloaded {self.outfile}")

    def filesize_unknown(self) -> bool:
        """Return True if the filesize is unknown."""
        return self.filesize_mb <= 0


@dataclass
class ExtractAssetCollection:
    """A collection of assets to be extracted from a collection of ExtractAsset objects.

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

    def num_assets_with_unknown_size(self) -> int:
        """Return the number of assets with unknown size."""
        return sum(1 for asset in self if asset.filesize_mb <= 0)

    def num_assets_to_download(self) -> int:
        """Return the number of assets to download."""
        return sum(1 for asset in self if not asset.downloaded)

    def num_assets_downloaded(self) -> int:
        """Return the number of assets already downloaded."""
        return sum(1 for asset in self if asset.downloaded)

    def total_size(self) -> int:
        """Return the total size (in MB) of all assets in the collection."""
        return sum(asset.filesize_mb for asset in self if asset.filesize_mb > 0)

    def total_undownloaded_size(self) -> int:
        """Return the total size (in MB) of all assets in the collection."""
        return sum(asset.filesize_mb for asset in self if asset.filesize_mb > 0 and not asset.downloaded)

    def summary(self) -> None:
        """Print a summary of the collection."""
        assets_types: Dict[str, str] = {}
        for ast in self:
            desc = ""
            if ast.asset.title:
                desc += ast.asset.title
            if ast.asset.description:
                desc += f" ({ast.asset.description})"
            assets_types[ast.asset_name] = desc
            logger.debug(f"\n{ast.id} ({ast.dtype}): {ast.filesize_mb} MB")
        ast_type_str = "\n" + "\n".join(
            [f'key={k}; description="{v}"' for k, v in assets_types.items()]
        )
        logger.info(f"Asset types: {ast_type_str}")
        logger.info(f"Total asset size: {self.total_size():,} MB")
        logger.info(f"Total undownloaded asset size: {self.total_undownloaded_size():,} MB")
        if self.num_assets_with_unknown_size() > 0:
            logger.info(
                f"Number of assets with unknown size: {self.number_of_assets_with_unknown_size()}"
            )

    def add_asset(self, asset: ExtractAsset) -> None:
        """Add an asset to the collection."""
        if asset.id not in self.assets:
            self.assets[asset.id] = []
        self.assets[asset.id].append(asset)
