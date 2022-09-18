"""Exposes access to providers, such as Microsoft Planetary Computer."""
from typing import Any, List

from ..config import CollectionSchema, ConfigSchema, ProviderKey
from .base import BaseProvider
from .earthdata import EarthDataProvider
from .mpc import MicrosoftPlanetaryComputer
from .radiant_ml import RadiantMLHub

__all__ = [
    "get_provider",
    "ProviderKey",
    "BaseProvider",
    "MicrosoftPlanetaryComputer",
    "EarthDataProvider",
]


def get_provider(
    id: ProviderKey,
    cfg: ConfigSchema,
    collections: List[CollectionSchema],
    **kwargs: Any,
) -> BaseProvider:
    """Get and initialize a provider instance by name."""
    if id == ProviderKey.MPC:
        return MicrosoftPlanetaryComputer(id, cfg, collections, **kwargs)
    elif id == ProviderKey.EARTHDATA:
        return EarthDataProvider(id, cfg, collections, **kwargs)
    elif id == ProviderKey.RADIANT:
        return RadiantMLHub(id, cfg, collections, **kwargs)
    else:
        raise ValueError(f"Unknown provider {id}")
