"""Exposes access to providers, such as Microsoft Planetary Computer."""
from typing import Any

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


def get_provider(id: ProviderKey, cfg: ConfigSchema, collections: CollectionSchema, **kwargs: Any) -> BaseProvider:
    """Get and initialize a provider instance by name."""
    provider: BaseProvider
    if id == ProviderKey.MPC:
        provider = MicrosoftPlanetaryComputer
    elif id == ProviderKey.EARTHDATA:
        provider = EarthDataProvider
    elif id == ProviderKey.RADIANT:
        provider = RadiantMLHub
    else:
        raise ValueError(f"Unknown provider {id}")

    return provider(id, cfg, collections, **kwargs)
