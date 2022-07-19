from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from metaearth.provider import ProviderKey

@dataclass
class SystemSchema:
    log_outdir: str = field(default="./logs")
    log_level: str = "INFO"
    dry_run: bool = False
    max_concurrent_extractions: int = 16
    max_download_retries: int = 3
    remove_existing_if_wrong_size: bool = False
    
@dataclass
class ProviderSchema:
    name: ProviderKey
    kwargs: Dict[str, Any] = field(default_factory=dict)
    
@dataclass
class CollectionSchema:
    provider: Optional[ProviderSchema] = None
    assets: Optional[List[str]] = None
    outdir: Optional[str] = None
    datetime: Optional[str] = None
    aoi_file: Optional[str] = None

@dataclass
class ConfigSchema:
    default_collection: CollectionSchema = field(default_factory=CollectionSchema)
    collections: Dict[str, CollectionSchema] = field(default_factory=dict)
    system: SystemSchema = field(default_factory=SystemSchema)

def get_collection_val_or_default(cfg: ConfigSchema, collection_name: str, key: str) -> Any:
    """Get a value from a collection or the default collection if it doesn't exist"""
    if cfg.collections[collection_name][key] is not None:
        return cfg.collections[collection_name][key]
    elif cfg.default_collection[key] is not None:
        return cfg.default_collection[key]
    else:
        raise ValueError(f"No value for {key} in collection {collection_name} and no default value")