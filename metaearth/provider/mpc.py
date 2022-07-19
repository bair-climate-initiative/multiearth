#!/usr/bin/env python

from typing import Iterator, List, Optional, Union

import planetary_computer as pc
import pystac
import shapely
from pystac_client import Client

from .base import BaseProvider


class MicrosoftPlanetaryComputer(BaseProvider):
    """
    Download data and extract assets from the Microsoft Planetary Computer.
    """
    _client: Optional[Client] = None

    def __init__(self, client_url="https://planetarycomputer.microsoft.com/api/stac/v1") -> None:
        """Setup the client to MPC
        """
        self._client = Client.open(
            client_url,
            ignore_conformance=True,
        )

    def __repr__(self) -> str:
        return "MicrosoftPlanetaryComputer Provider"
    
    # abstract method override
    def region_to_items(
        self,
        region: Union[shapely.geometry.Polygon, shapely.geometry.MultiPolygon],
        datetime: str,
        collections: List[str]
    ) -> Iterator[pystac.Item]: 
 
        search = self._client.search(
            datetime=datetime,
            collections=collections, 
            intersects=region,
            max_items=10000  # this is the max setting for MPC
          )
        return search.items()
            

    # method override
    def asset_to_download_url(self, asset: pystac.Asset) -> str:
        return pc.sign(asset.href)
