from typing import List, Union

import shapely
import pystac
import pandas as pd
from loguru import logger


def region_to_stac_item_collection(
    credentials: str,
    region: Union[shapely.geometry.Polygon, shapely.geometry.MultiPolygon],
    start_date: str,
    end_date: str,
    constellations: List[str],
) -> pystac.ItemCollection:
    """Create STAC ItemCollection for a given region, where the region is typically parsed from a geojson file.
    Args:
        credentials (str): The bigquery client credentials json path
        region (Union[shapely.geometry.Polygon, shapely.geometry.MultiPolygon]): the region
        start_date (str): sensing start date
        end_date (str): sensing end date
    Returns:
        pystac.ItemCollection: a item collection for the given region and dates
    """

    dfs = []

    for constellation in constellations:

        if constellation == "sentinel-2":
            df = get_sentinel_2_assets_df(client, region, start_date, end_date)
        else:
            df = get_landsat_assets_df(
                client,
                region,
                start_date,
                end_date,
                constellation,
            )

        df["constellation"] = constellation
        dfs.append(df)

    df = pd.concat(dfs)

    return create_stac_item_collection_from_df(df)




""" client = Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    ignore_conformance=True,
) """