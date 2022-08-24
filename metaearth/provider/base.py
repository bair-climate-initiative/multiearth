"""Provides an abstract base class for all providers."""

from abc import ABC
from typing import Iterator, Union

import pystac
import shapely
import shapely.geometry
from pystac_client import Client


class BaseProvider(ABC):
    """Abstract base class describing the provider interface."""

    def region_to_items(
        self,
        region: Union[shapely.geometry.Polygon, shapely.geometry.MultiPolygon],
        datetime: str,
        collection: str,
        max_items: int,
    ) -> Iterator[pystac.Item]:
        """Create stac ItemCollection from a given region between start_date and end_date.

        Args:
            region (Union[shapely.geometry.Polygon, shapely.geometry.MultiPolygon]): the region
            datetime (str): Single date+time, or a range ('/' separator), formatted to RFC 3339,
                section 5.6. Use double dots .. for open date ranges.
            collection (str): collection to include in the returned ItemCollection
            max_items (int): maximum number of items to return, -1 for no limit/provider limit
        Returns:
            Iterator[pystac.Item]: an iterable that contains the pystac items
        """
        pass

    def asset_to_download_url(self, asset: pystac.Asset) -> str:
        """Take a single input item and return a download url.

        Args:
            asset (pystac.Asset): a STAC asset
        Returns:
            str: a download url for the given item
        """
        return_url: str = asset.href
        return return_url


class STACProvider(BaseProvider):
    """Provides standard STAC API region_to_items method."""

    # max items allowed client
    _max_items: int = 10000
    _description: str
    _default_client_url: str

    def __init__(self, client_url: str = "") -> None:
        """Set up the STAC client."""
        if client_url == "":
            client_url = self._default_client_url
        self._client = Client.open(client_url, ignore_conformance=True)
        if not self.check_authorization():
            raise Exception(
                f"{self} is not authorized. See the documentation for {self}."
            )

    def __repr__(self) -> str:
        """Return a string representation of the provider."""
        return self._description

    def check_authorization(self) -> bool:
        """Check if the provider is authorized - meant to be overridden."""
        return True

    def region_to_items(
        self,
        region: Union[shapely.geometry.Polygon, shapely.geometry.MultiPolygon],
        datetime: str,
        collection: str,
        max_items: int,
    ) -> Iterator[pystac.Item]:
        """Search the STAC Client with a given region and date in order to obtain STAC items."""
        if max_items < 0:
            max_items = self._max_items
        search = self._client.search(
            datetime=datetime,
            collections=collection,
            intersects=region,
            max_items=max_items,
        )
        items: Iterator[pystac.Item] = search.items()
        return items
