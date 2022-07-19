from abc import ABC, abstractmethod
from typing import Any, Iterator, List, Union

import pystac
import shapely

class BaseProvider(ABC):
    """
    Abstract base class describing the provider interface
    """
    regions = []

    def add_region(self, region: Any) -> None:
        """
        Add a region to be extracted using the provider.
        """
        self.regions.append(region)
    
    @abstractmethod
    def region_to_items(
        self,
        region: Union[shapely.geometry.Polygon, shapely.geometry.MultiPolygon],
        datetime: str,
        collections: List[str]
    ) -> Iterator[pystac.Item]:
        """Create stac ItemCollection from a given region between start_date and end_date.

        Args:
            region (Union[shapely.geometry.Polygon, shapely.geometry.MultiPolygon]): the region
            datetime (str): Single date+time, or a range ('/' separator), formatted to RFC 3339, section 5.6. Use double dots .. for open date ranges.
            collections (List[str]): list of collections to include in the ItemCollection
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
        return asset.href
    