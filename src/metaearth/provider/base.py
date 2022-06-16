from abc import ABC, abstractmethod
from typing import Iterator, List, Union

import pystac
import shapely
from omegaconf import DictConfig

class BaseProvider(ABC):
    """
    Abstract base class describing the provider interface
    """
    
    @abstractmethod
    def region_to_items(
        self,
        region: Union[shapely.geometry.Polygon, shapely.geometry.MultiPolygon],
        start_date: str,
        end_date: str,
        collections: List[str]
    ) -> Iterator[pystac.Item]:
        """Create stac ItemCollection from a given region between start_date and end_date.

        Args:
            region (Union[shapely.geometry.Polygon, shapely.geometry.MultiPolygon]): the region
            start_date (str): sensing start date
            end_date (str): sensing end date
            collections (List[str]): list of collections to include in the ItemCollection
        Returns:
            Iterator[pystac.Item]: an iterable that contains the pystac items
        """
        pass
    
    @abstractmethod
    def item_to_download_url(self, item: pystac.Item) -> str:
        """Take a single input item and return a download url.

        Args:
            item (pystac.ItemCollection): a item collection for the given region and dates
        Returns:
            str: a download url for the given item
        """
        pass
    