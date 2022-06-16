#!/usr/bin/env python

from typing import Iterator, List, Union, Optional

import pystac
from pystac_client import Client
import shapely
import planetary_computer as pc

from .base import BaseProvider


class MicrosoftPlanetaryComputer(BaseProvider):
    """
    TODO(cjrd) describe how MPC works and provide relevant doc links
    """
    _client: Optional[Client] = None

    def __init__(self) -> None:
        """Setup the client to MPC
        """
        self._client = Client.open(
            "https://planetarycomputer.microsoft.com/api/stac/v1",
            ignore_conformance=True,
        )

    def __repr__(self) -> str:
        return "MicrosoftPlanetaryComputer Provider"

    # abstract method override
    def region_to_items(
        self,
        region: Union[shapely.geometry.Polygon, shapely.geometry.MultiPolygon],
        start_date: str,
        end_date: str,
        collections: List[str]
    ) -> Iterator[pystac.Item]:

        search = self._client.search(
              collections=collections, 
              intersects=region,
              max_items=10000  # this is the max setting for MPC
          )
        return search.items()
            

    # abstract method override
    def item_to_download_url(self, item: pystac.Item) -> str:
        pass