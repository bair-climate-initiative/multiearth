from typing import List, Type

import geopandas as gpd
from metloom.pointdata.cdec import CDECPointData
from metloom.pointdata.snotel import SnotelPointData
from metloom.variables import SnotelVariables

from metaearth.provider.base import STACProvider

# from .earthdata_providers import EARTHDATA_PROVIDERS

# class SnotelProvider(STACProvider):
#     """Download data and extract assets from the Microsoft Planetary Computer."""

#     _client: SnotelClient
#     _description: str = "Microsoft Planetary Computer (MPC)"
#     _default_client_url: str = "https://planetarycomputer.microsoft.com/api/stac/v1"

#     # method override
#     def asset_to_download_url(self, asset: pystac.Asset) -> str:
#         """Sign the asset url with the MPC client and return URL."""
#         return_url: str = pc.sign(asset.href)
#         return return_url


class SnotelClient(SnotelPointData):
    """SnotelClient used by SnotelProvider."""

    pass


class CDECClient(CDECPointData):
    """CDECClient used by CDECProvider."""

    pass


class MetloomProvider(STACProvider):
    """Metloom Provider."""

    _client: Type[SnotelClient] = SnotelClient
    _description: str
    _default_client_url: str
    _allowed_variables: dict

    def __init__(self) -> None:
        pass

    # method override
    def region_to_items(
        self,
        region: gpd.GeoDataFrame,
        datetime: str,
        collection: str,
        max_items: int,
        variables: List[str],
    ) -> gpd.GeoDataFrame:
        """
        Return a dataframe of location name, triplet id,
        datasource (likely NRCS for SNOTEL), and geometry
        """
        variables = [self._allowed_variables[variable] for variable in variables]
        regions = self._client.points_from_geometry(
            region, variables, dates=datetime, max_items=max_items
        )
        return regions


class SnotelProvider(MetloomProvider):
    """Snotel Provider.

    https://www.nrcs.usda.gov/wps/portal/wcc/home/snowClimateMonitoring/snowpack/snotelSensorData/
    """

    _client: Type[SnotelClient] = SnotelClient
    _description: str = "Snotel"
    _default_client_url: str = (
        "https://wcc.sc.egov.usda.gov/awdbWebService/services?WSDL"
    )
    _allowed_variables = {
        "WTEQ": SnotelVariables.SWE,
        "SWE": SnotelVariables.SWE,
        "SNWD": SnotelVariables.SNOWDEPTH,
        "SNOW_DEPTH": SnotelVariables.SNOWDEPTH,
        "TOBS": SnotelVariables.TEMP,
        "AIR TEMP": SnotelVariables.TEMP,
        "TAVG": SnotelVariables.TEMPAVG,
        "TMIN": SnotelVariables.TEMPMIN,
        "TMAX": SnotelVariables.TEMPMAX,
        "PRCPSA": SnotelVariables.PRECIPITATION,
        "PRECIPITATION": SnotelVariables.PRECIPITATION,
    }

    # def extract_assets_from_item(self, station_id: str):
    #     pass


class CDECProvider(MetloomProvider):
    """Snotel Provider.

    https://www.nrcs.usda.gov/wps/portal/wcc/home/snowClimateMonitoring/snowpack/snotelSensorData/
    """

    _client: Type[SnotelClient] = SnotelClient
    _description: str = "Snotel"
    _default_client_url: str = (
        "https://wcc.sc.egov.usda.gov/awdbWebService/services?WSDL"
    )
    _allowed_variables = {
        "WTEQ": SnotelVariables.SWE,
        "SWE": SnotelVariables.SWE,
        "SNWD": SnotelVariables.SNOWDEPTH,
        "SNOW_DEPTH": SnotelVariables.SNOWDEPTH,
        "TOBS": SnotelVariables.TEMP,
        "AIR TEMP": SnotelVariables.TEMP,
        "TAVG": SnotelVariables.TEMPAVG,
        "TMIN": SnotelVariables.TEMPMIN,
        "TMAX": SnotelVariables.TEMPMAX,
        "PRCPSA": SnotelVariables.PRECIPITATION,
        "PRECIPITATION": SnotelVariables.PRECIPITATION,
    }
