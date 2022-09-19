"""Microsoft Planetary Computer (MPC) provider."""

from typing import Callable

import planetary_computer as pc
import pystac

from .stac import STACProvider


class MicrosoftPlanetaryComputer(STACProvider):
    """Download data and extract assets from the Microsoft Planetary Computer."""

    _default_client_url: str = "https://planetarycomputer.microsoft.com/api/stac/v1"
    description: str = "Microsoft Planetary Computer (MPC)"

    # method override
    def _get_asset_to_download_url_fn(self) -> Callable[[pystac.Asset], str]:
        """Sign the asset url with the MPC client and return URL."""
        return _asset_to_download_url


def _asset_to_download_url(asset: pystac.Asset) -> str:
    """Sign the asset url with the MPC client and return URL."""
    return str(pc.sign(asset.href))
