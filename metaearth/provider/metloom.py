"""Metloom Provider.

https://github.com/M3Works/metloom
"""
import pickle
from datetime import datetime
from functools import reduce
from typing import Any, Dict, List, Type

import geopandas as gpd
import pandas as pd
from metloom.dataframe_utils import append_df
from metloom.pointdata.base import PointData
from metloom.pointdata.cdec import CDECPointData
from metloom.pointdata.snotel import SnotelPointData
from metloom.pointdata.snotel_client import (
    MetaDataSnotelClient,
    PointSearchSnotelClient,
)
from metloom.variables import (
    CdecStationVariables,
    SensorDescription,
    SnotelVariables,
    VariableBase,
)

from metaearth.config import CollectionSchema, ConfigSchema, ProviderKey
from metaearth.provider.base import BaseProvider


class SnotelClient(SnotelPointData):  # type: ignore
    """SnotelClient used by SnotelProvider."""

    def points_from_geometry(
        cls,
        geometry: gpd.GeoDataFrame,
        variables: List[SensorDescription],
        start_date: datetime,
        end_date: datetime,
        max_items: int = -1,
        **kwargs: Any,
    ) -> PointData.ITERATOR_CLASS:
        """
        See docstring for PointData.points_from_geometry.

        Args:
            geometry: GeoDataFrame for shapefile from gpd.read_file
            variables: List of SensorDescription
            snow_courses: boolean for including only snowcourse data or no
                snowcourse data
            within_geometry: filter the points to within the shapefile
                instead of just the extents. Default True
            buffer: buffer added to search box
        Returns:
            PointDataCollection
        """
        # assign defaults
        kwargs = cls._add_default_kwargs(kwargs)

        projected_geom = geometry.to_crs(4326)
        bounds = projected_geom.bounds.iloc[0]

        network = "SNOW" if kwargs["snow_courses"] else ["SNTL", "USGS", "BOR", "COOP"]
        point_codes = []
        buffer = kwargs["buffer"]
        search_kwargs = {
            "max_latitude": bounds["maxy"] + buffer,
            "min_latitude": bounds["miny"] - buffer,
            "max_longitude": bounds["maxx"] + buffer,
            "min_longitude": bounds["minx"] - buffer,
            "network_cds": network,
        }
        for variable in variables:
            response = PointSearchSnotelClient(
                element_cds=variable.code, **search_kwargs
            ).get_data()
            if len(response) > 0:
                point_codes += response

        # no duplicate codes
        point_codes = list(set(point_codes))
        dfs = []
        for ind, code in enumerate(point_codes):
            dfs.append(
                pd.DataFrame.from_records(
                    [MetaDataSnotelClient(station_triplet=code).get_data()]
                ).set_index("stationTriplet")
            )

        if len(dfs) > 0:
            df = reduce(lambda a, b: append_df(a, b), dfs)
        else:
            return cls.ITERATOR_CLASS([])

        df.reset_index(inplace=True)
        gdf = gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(
                df["longitude"], df["latitude"], z=df["elevation"]
            ),
        )
        if kwargs["within_geometry"]:
            filtered_gdf = gdf[gdf.within(projected_geom.iloc[0]["geometry"])]
        else:
            filtered_gdf = gdf
        if start_date is not None:
            filtered_gdf = filtered_gdf[
                pd.to_datetime(filtered_gdf["beginDate"], format="%Y-%m-%d")
                < start_date
            ]
        if end_date is not None:
            filtered_gdf = filtered_gdf[
                pd.to_datetime(filtered_gdf["endDate"], format="%Y-%m-%d") > end_date
            ]
        points = []
        for i, row in enumerate(
            zip(
                filtered_gdf["stationTriplet"],
                filtered_gdf["name"],
                filtered_gdf["geometry"],
            )
        ):
            if i == max_items:
                break
            points.append(cls(row[0], row[1], metadata=row[2]))
        # points = [
        #     cls(row[0], row[1], metadata=row[2])
        #     for row in zip(
        #         filtered_gdf["stationTriplet"],
        #         filtered_gdf["name"],
        #         filtered_gdf["geometry"],
        #     )
        # ]
        return cls.ITERATOR_CLASS(points)


class CdecClient(CDECPointData):  # type: ignore
    """SnotelClient used by SnotelProvider."""

    def points_from_geometry(
        cls,
        geometry: gpd.GeoDataFrame,
        variables: List[SensorDescription],
        max_items: int = -1,
        **kwargs: Any,
    ) -> PointData.ITERATOR_CLASS:
        """
        See docstring for PointData.points_from_geometry.

        Args:
            geometry: GeoDataFrame for shapefile from gpd.read_file
            variables: List of SensorDescription
            snow_courses: Boolean for including only snowcourse data or no
            snowcourse data
            within_geometry: filter the points to within the shapefile
            instead of just the extents. Default True
            buffer: buffer added to search box

        Returns:
            PointDataCollection
        """
        # assign defaults
        kwargs = cls._add_default_kwargs(kwargs)

        # Assume station search result is in 4326
        projected_geom = geometry.to_crs(4326)
        bounds = projected_geom.bounds.iloc[0]
        search_df = None
        station_search_kwargs = {}

        # Filter to manual, monthly measurements if looking for snow courses
        if kwargs["snow_courses"]:
            station_search_kwargs["dur"] = "M"
            station_search_kwargs["collect"] = "MANUAL+ENTRY"
        for variable in variables:
            result_df = cls._station_sensor_search(
                bounds, variable, buffer=kwargs["buffer"], **station_search_kwargs
            )
            if result_df is not None:
                result_df["index_id"] = result_df["ID"]
                result_df.set_index("index_id", inplace=True)
                search_df = append_df(search_df, result_df).drop_duplicates(
                    subset=["ID"]
                )
        # return empty collection if we didn't find any points
        if search_df is None:
            return cls.ITERATOR_CLASS([])
        gdf = gpd.GeoDataFrame(
            search_df,
            geometry=gpd.points_from_xy(
                search_df["Longitude"],
                search_df["Latitude"],
                z=search_df["ElevationFeet"],
            ),
        )
        # filter to points within shapefile
        if kwargs["within_geometry"]:
            filtered_gdf = gdf[gdf.within(projected_geom.iloc[0]["geometry"])]
        else:
            filtered_gdf = gdf
        points = []
        for i, row in enumerate(
            zip(
                filtered_gdf.index,
                filtered_gdf["Station Name"],
                filtered_gdf["geometry"],
            )
        ):
            if i == max_items:
                break
            points.append(cls(row[0], row[1], metadata=row[2]))
        # points = [
        #     cls(row[0], row[1], metadata=row[2])
        #     for row in zip(
        #         filtered_gdf.index,
        #         filtered_gdf["Station Name"],
        #         filtered_gdf["geometry"],
        #     )
        # ]
        # filter to snow courses or not snowcourses depending on desired result
        if kwargs["snow_courses"]:
            return cls.ITERATOR_CLASS([p for p in points if p.is_partly_snow_course()])
        else:
            return cls.ITERATOR_CLASS(
                [p for p in points if not p.is_only_snow_course(variables)]
            )


class MetloomProvider(BaseProvider):
    """Metloom Provider."""

    description: str = "Metloom Provider (METLOOM)"
    _client: Type[PointData]
    _clients: Dict[str, Type[PointData]] = {"SNOTEL": SnotelClient, "CDEC": CdecClient}

    _default_client_url: str
    _allowed_assets: Dict[str, Dict[str, VariableBase]] = {
        "SNOTEL": {
            "WTEQ": SnotelVariables.SWE,
            "SWE": SnotelVariables.SWE,
            "SNWD": SnotelVariables.SNOWDEPTH,
            "SNOW_DEPTH": SnotelVariables.SNOWDEPTH,
            "TOBS": SnotelVariables.TEMP,
            "AIR TEMP": SnotelVariables.TEMP,
            "TAVG": SnotelVariables.TEMPAVG,
            "TEMPAVG": SnotelVariables.TEMPAVG,
            "TMIN": SnotelVariables.TEMPMIN,
            "TEMPMIN": SnotelVariables.TEMPMIN,
            "TMAX": SnotelVariables.TEMPMAX,
            "TEMPMAX": SnotelVariables.TEMPMAX,
            "PRCPSA": SnotelVariables.PRECIPITATION,
            "PRECIPITATION": SnotelVariables.PRECIPITATION,
            "RH": SnotelVariables.RH,
        },
        "CDEC": {
            "WTEQ": CdecStationVariables.SWE,
            "SWE": CdecStationVariables.SWE,
            "SNWD": CdecStationVariables.SNOWDEPTH,
            "SNOW_DEPTH": CdecStationVariables.SNOWDEPTH,
            "TEMP": CdecStationVariables.TEMP,
            "TAVG": CdecStationVariables.TEMPAVG,
            "TEMPAVG": CdecStationVariables.TEMPAVG,
            "TMIN": CdecStationVariables.TEMPMIN,
            "TEMPMIN": CdecStationVariables.TEMPMIN,
            "TMAX": CdecStationVariables.TEMPMAX,
            "TEMPMAX": CdecStationVariables.TEMPMAX,
            "PRCPSA": CdecStationVariables.PRECIPITATION,
            "PRECIPITATION": CdecStationVariables.PRECIPITATION,
            "RH": CdecStationVariables.RH,
        },
    }
    _allowed_datasets: List[str] = ["SNOTEL", "CDEC"]
    _locations: Dict[str, gpd.GeoDataFrame] = {}
    _assets: Dict[str, List[str]] = {}

    def __init__(
        self,
        id: ProviderKey,
        cfg: ConfigSchema,
        collections: List[CollectionSchema],
        **kwargs: Any,
    ) -> None:
        """Initialize Metloom Provider."""
        super().__init__(id, cfg, collections, **kwargs)

    def check_authorization(self) -> bool:
        """Check if the provider is authorized."""
        return True

    def extract_assets(self, dry_run: bool = False) -> bool:
        """Download a dataset to assigned output_dir."""
        for collection in self.collections:
            if dry_run:
                collection.max_items = 10
            dataset_id = collection.id
            assert (
                dataset_id in self._allowed_datasets
            ), f"Collection {dataset_id} does not exist in Radiant ML Hub"
            assert (
                collection.datetime is not None
            ), "Collection {dataset_id} datetime is not set"
            assert (
                collection.outdir is not None
            ), "Collection {dataset_id} outdir is not set"
            allowed_assets = self._allowed_assets[dataset_id]
            assert collection.assets is not None
            assert all(
                asset in allowed_assets for asset in collection.assets
            ), "asset is not in allowed assets"
            self._client = self._clients[dataset_id]
            assets = [allowed_assets[asset] for asset in collection.assets]
            start_date_temp, end_date_temp = collection.datetime.split("/")
            start_date = datetime.strptime(start_date_temp, "%Y-%m-%d")
            end_date = datetime.strptime(end_date_temp, "%Y-%m-%d")
            if collection.aoi_file is not None:
                region = gpd.read_file(collection.aoi_file)
            self._locations[dataset_id] = self._region_to_items(
                region,
                start_date,
                end_date,
                collection.assets,
                dataset_id,
                collection.max_items,
            )
            daily_data = []
            for location in self._locations[dataset_id].to_dataframe()["id"]:
                daily_data.append(
                    self._client(location, "MyStation").get_daily_data(
                        start_date, end_date, assets
                    )
                )
            self._assets[dataset_id] = daily_data

            if dry_run:
                continue
            with open(f"{collection.outdir}/{dataset_id}.pkl", "wb") as f:
                pickle.dump(self._assets[dataset_id], f)

        return True

    # method override
    def _region_to_items(
        self,
        region: gpd.GeoDataFrame,
        start_date: datetime,
        end_date: datetime,
        collection: List[str],
        id: str,
        max_items: int = -1,
    ) -> gpd.GeoDataFrame:
        """Return a dataframe of regions.

        Dataframe consists of location name, triplet id, datasource (likely NRCS for SNOTEL),
        and geometry.
        """
        variables = [self._allowed_assets[id][variable] for variable in collection]
        self.collections = variables
        regions = self._client.points_from_geometry(
            region,
            variables,
            start_date=start_date,
            end_date=end_date,
            max_items=max_items,
        )
        return regions


class SnotelProvider(MetloomProvider):
    """Snotel Provider.

    https://www.nrcs.usda.gov/wps/portal/wcc/home/snowClimateMonitoring/snowpack/snotelSensorData/
    """

    _client: Type[SnotelPointData] = SnotelPointData
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

    def extract_assets(self, dry_run: bool = False) -> bool:
        """Extract assets from the collections in the configuration.

        Returns: True if all assets extracted successfully, False otherwise.
        """
        pass


class CDECProvider(MetloomProvider):
    """Snotel Provider.

    https://www.nrcs.usda.gov/wps/portal/wcc/home/snowClimateMonitoring/snowpack/snotelSensorData/
    """

    _client: Type[SnotelPointData] = SnotelPointData
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
