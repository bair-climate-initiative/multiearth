"""Config schema for MetaEarth config."""
import typing
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from omegaconf import DictConfig


class ProviderKey(Enum):
    """Helper class for identifying providers."""
    # import here to avoid circular import
    MPC = "MicrosoftPlanetaryComputer"
    EARTHDATA = "EarthDataProvider"
    RADIANT = "RadiantMLHub"


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
class CollectionSchema:
    """Collection config schema for MetaEarth config."""
    id: Optional[str] = None
    assets: Optional[List[str]] = None
    outdir: Optional[str] = None
    datetime: Optional[str] = None
    aoi_file: Optional[str] = None
    max_items: int = -1


@dataclass
class ProviderSchema:
    """Provider config schema for MetaEarth config."""
    id: ProviderKey
    kwargs: Dict[str, Any] = field(default_factory=dict)
    collections: List[CollectionSchema] = field(default_factory=list)


@dataclass
class ConfigSchema:
    """Top-level config schema for MetaEarth config."""
    default_collection: CollectionSchema = field(default_factory=CollectionSchema)
    providers: List[ProviderSchema] = field(default_factory=list)
    system: SystemSchema = field(default_factory=SystemSchema)
    run_id: str = field(default="") # computed run id


def get_collection_val_or_default(
    cfg: ConfigSchema, pvdr_id: ProviderKey, collection_name: str, key: str
) -> Any:
    """Get a value from a collection or the default collection if it doesn't exist."""
    coll = typing.cast(DictConfig, cfg.providers[pvdr_id].collections[collection_name])
    def_coll = typing.cast(DictConfig, cfg.default_collection)
    if coll[key] is not None:
        return coll[key]
    elif def_coll[key] is not None:
        return def_coll[key]
    else:
        raise ValueError(
            f"No value for {key} in collection {collection_name} and no default value"
        )
