"""Exposes access to providers, such as Microsoft Planetary Computer."""
from enum import Enum
from typing import Any

from metaearth.provider.radiant_ml import RadiantMLHub
from metaearth.util.misc import dict_hash

from .base import BaseProvider
from .earthdata import EarthDataProvider
from .mpc import MicrosoftPlanetaryComputer

__all__ = [
    "get_provider",
    "ProviderKey",
    "BaseProvider",
    "MicrosoftPlanetaryComputer",
    "EarthDataProvider",
]


class ProviderKey(Enum):
    """Helper class for identifying providers."""

    MPC = MicrosoftPlanetaryComputer
    EARTHDATA = EarthDataProvider
    RADIANT = RadiantMLHub


# keep track of providers instantiated with given args
_provider_store = {}


def get_provider(provider_name: ProviderKey, **kwargs: Any) -> BaseProvider:
    """Get a provider instance by name."""
    args_hash = dict_hash(kwargs)
    key_str = f"{provider_name}_{args_hash}"
    if key_str not in _provider_store:
        # create provider instance since it doesn't exist in the store with given args
        provider: BaseProvider
        if provider_name == ProviderKey.MPC:
            provider = MicrosoftPlanetaryComputer(**kwargs)
        elif provider_name == ProviderKey.EARTHDATA:
            provider = EarthDataProvider(**kwargs)
        elif provider_name == ProviderKey.RADIANT:
            provider = RadiantMLHub(**kwargs)
        else:
            raise ValueError(f"Unknown provider {provider_name}")

        if provider is not None:
            _provider_store[key_str] = provider

    return _provider_store[key_str]
