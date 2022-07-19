"""Microsoft Planetary Computer (MPC) provider."""

from typing import Iterator, Union

import planetary_computer as pc
import pystac
import shapely
from pystac_client import Client

from .base import BaseProvider


class MicrosoftPlanetaryComputer(BaseProvider):
    """Download data and extract assets from the Microsoft Planetary Computer."""

    _client: Client

    def __init__(
        self, client_url: str = "https://planetarycomputer.microsoft.com/api/stac/v1"
    ) -> None:
        """Setup the client to MPC."""
        self._client = Client.open(client_url, ignore_conformance=True)

    def __repr__(self) -> str:
        """Return a string representation of the provider."""
        return "MicrosoftPlanetaryComputer Provider"

    # abstract method override
    def region_to_items(
        self,
        region: Union[shapely.geometry.Polygon, shapely.geometry.MultiPolygon],
        datetime: str,
        collection: str,
    ) -> Iterator[pystac.Item]:
        """Search the STAC Client with a given region and date in order to obtain STAC items."""
        search = self._client.search(
            datetime=datetime,
            collections=collection,
            intersects=region,
            max_items=10000,  # this is the max setting for MPC
        )
        items: Iterator[pystac.Item] = search.items()
        return items

    # method override
    def asset_to_download_url(self, asset: pystac.Asset) -> str:
        """Sign the asset url with the MPC client and return URL."""
        return_url: str = pc.sign(asset.href)
        return return_url
