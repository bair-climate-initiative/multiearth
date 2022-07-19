"""Provides an abstract base class for all providers."""

from abc import ABC, abstractmethod
from typing import Iterator, List, Union

import pystac
import shapely


class BaseProvider(ABC):
    """Abstract base class describing the provider interface."""

    regions: List[Union[shapely.geometry.Polygon, shapely.geometry.MultiPolygon]] = []

    def add_region(
        self, region: Union[shapely.geometry.Polygon, shapely.geometry.MultiPolygon]
    ) -> None:
        """Add a region to be extracted using the provider.

        Args:
            region (shapely.geometry.Polygon): a region to extract
        Returns:
            None
        """
        self.regions.append(region)

    @abstractmethod
    def region_to_items(
        self,
        region: Union[shapely.geometry.Polygon, shapely.geometry.MultiPolygon],
        datetime: str,
        collection: str,
    ) -> Iterator[pystac.Item]:
        """Create stac ItemCollection from a given region between start_date and end_date.

        Args:
            region (Union[shapely.geometry.Polygon, shapely.geometry.MultiPolygon]): the region
            datetime (str): Single date+time, or a range ('/' separator), formatted to RFC 3339,
                section 5.6. Use double dots .. for open date ranges.
            collection (str): collection to include in the returned ItemCollection
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
