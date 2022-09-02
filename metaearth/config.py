"""Config schema for MetaEarth config."""
import typing
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from omegaconf import DictConfig

from .provider import ProviderKey


@dataclass
class SystemSchema:
    """System config schema for MetaEarth config."""

    log_outdir: str = field(default="./logs")
    log_level: str = "INFO"
    dry_run: bool = False
    max_concurrent_extractions: int = 10
    max_download_attempts: int = 3
    remove_existing_if_wrong_size: bool = False
    query_asset_sizes: bool = True


@dataclass
class ProviderSchema:
    """Provider config schema for MetaEarth config."""

    name: ProviderKey
    kwargs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CollectionSchema:
    """Collection config schema for MetaEarth config."""

    provider: Optional[ProviderSchema] = None
    assets: Optional[List[str]] = None
    outdir: Optional[str] = None
    datetime: Optional[str] = None
    aoi_file: Optional[str] = None
    max_items: int = -1


@dataclass
class ConfigSchema:
    """Top-level config schema for MetaEarth config."""

    default_collection: CollectionSchema = field(default_factory=CollectionSchema)
    collections: Dict[str, CollectionSchema] = field(default_factory=dict)
    system: SystemSchema = field(default_factory=SystemSchema)


def get_collection_val_or_default(
    cfg: ConfigSchema, collection_name: str, key: str
) -> Any:
    """Get a value from a collection or the default collection if it doesn't exist."""
    coll = typing.cast(DictConfig, cfg.collections[collection_name])
    def_coll = typing.cast(DictConfig, cfg.default_collection)
    if coll[key] is not None:
        return coll[key]
    elif def_coll[key] is not None:
        return def_coll[key]
    else:
        raise ValueError(
            f"No value for {key} in collection {collection_name} and no default value"
        )
