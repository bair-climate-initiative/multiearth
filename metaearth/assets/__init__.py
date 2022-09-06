"""Models for asset extraction and management."""
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Tuple

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
    download_kwargs: Dict[str, Any] = field(default_factory=dict)
    download_attempts: int = field(default=0)
    last_download_url: str = field(default="")
    asset: Any = field(default=None)

    def __call__(self) -> Any:
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
    provider_name: str = field(default="")
    collection_name: str = field(default="")

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
    _sep_str = "*" * 100

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
        return sum(
            asset.filesize_mb
            for asset in self
            if asset.filesize_mb > 0 and not asset.downloaded
        )

    def unique_providers(self) -> List[str]:
        """Return a str list of unique providers in the collection."""
        return list({ast.provider_name for ast in self})

    def unique_provider_collections(self) -> List[str]:
        """Return a str list of unique providers collections in the collection."""
        return list({ast.provider_name + ": " + ast.collection_name for ast in self})

    def summary(self) -> Tuple[str, str]:
        """Return a formatted summary of the collection for logging.

        Returns:
            Tuple[str, str]: a tuple of the summary string and a detailed debug summary string
        """
        pvdrs = "\n".join(sorted(self.unique_provider_collections()))
        summary = f"{self._sep_str}\n" "To Extract:\n" f"{pvdrs}\n"
        summary_details = "\nDETAILS\n"

        ast_summary = (
            f"{'Collection':<25}| {'Key':<20}| Description\n" + "-" * 80 + "\n"
        )
        added = dict()
        for ast in self:
            desc = ""
            if ast.asset.title:
                desc += ast.asset.title
            if ast.asset.description:
                desc += f" ({ast.asset.description})"

            hash_val = ast.collection_name + ast.asset_name + desc
            if hash_val in added:
                continue

            added[hash_val] = True
            ast_summary += f"{ast.collection_name:<25}| {ast.asset_name:<20}| {desc}\n"
            summary_details += f"\n{ast.id} ({ast.dtype}): {ast.filesize_mb} MB"

        summary += (
            f"\n\n{ast_summary}\n"
            f"\n{'Collection size':<35} {self.total_size():,} MB"
            f"\n{'Size of remaining data to download':<35} {self.total_undownloaded_size():,} MB"
        )
        if self.num_assets_with_unknown_size() > 0:
            summary += (
                "\nNumber of assets with unknown size:"
                f" {self.num_assets_with_unknown_size()}\n"
            )

        summary += f"\n{self._sep_str}\n"
        summary_details += f"\n{self._sep_str}\n"
        return summary, summary_details

    def add_asset(self, asset: ExtractAsset) -> None:
        """Add an asset to the collection."""
        if asset.id not in self.assets:
            self.assets[asset.id] = []
        self.assets[asset.id].append(asset)
