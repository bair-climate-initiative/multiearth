"""EarthData Provider.

https://www.radiant.earth
"""

import json
import os
from typing import Any, List

import dateutil.parser
from loguru import logger
from pystac_client.exceptions import APIError
from radiant_mlhub import Dataset

from metaearth.config import CollectionSchema, ConfigSchema, ProviderKey
from metaearth.provider.base import BaseProvider

from ..util.datetime import datetime_str_to_value


def _list_wrapper(f: Any) -> Any:
    """Modify a function to consider f([arg]) and f(arg) as equivalent.

    This is used to overwrite isoparse to handle the date format of LandCover Dataset
    TODO: Find a better way to handle this
    """

    def g(*args: Any, **kwargs: Any) -> Any:
        """Return first arg item of list if list."""
        largs = list(args)
        if isinstance(largs[0], list):
            return f(largs[0][0], *largs[1:], **kwargs)
        return f(*largs, **kwargs)

    return g


# TODO ugly shim - find a better workaround
dateutil.parser.isoparse = _list_wrapper(dateutil.parser.isoparse)


# import pystac_client after isoparse overwrite, overwrite flake8 checks
from pystac_client import Client  # noqa : E402


class RadiantMLHub(BaseProvider):
    """Download data and extract assets from the Radient ML Hub."""

    description: str = "Radiant ML Hub (RADIANT)"
    _client: Client
    _default_client_url: str = "https://api.radiant.earth/mlhub/v1"

    def __init__(
        self,
        id: ProviderKey,
        cfg: ConfigSchema,
        collections: List[CollectionSchema],
        client_url: str = "",
        api_key: str = "",
        **kwargs: Any,
    ) -> None:
        """Set up the STAC client."""
        if client_url == "":
            client_url = self._default_client_url
        if api_key == "":
            api_key = os.environ.get("MLHUB_API_KEY", "")
        self.api_key = api_key
        self._client = Client.open(
            client_url, ignore_conformance=True, parameters={"key": api_key}
        )

        super().__init__(id, cfg, collections, **kwargs)

    def check_authorization(self) -> bool:
        """Check if the provider is authorized."""
        try:
            assert self._client._stac_io, "STAC client is not initialized properly"
            self._client._stac_io.read_text("https://api.radiant.earth/mlhub/v1/search")
            return True
        except APIError:
            return False

    def extract_assets(self, dry_run: bool = False) -> bool:
        """Download a dataset to assigned output_dir."""
        all_datasets = [x.id for x in Dataset.list()]

        for collection in self.collections:
            dataset_id = collection.id
            assert (
                dataset_id in all_datasets
            ), f"Collection {dataset_id} does not exist in Radiant ML Hub"
            assert (
                collection.datetime is not None
            ), "Collection {dataset_id} datetime is not set"
            assert (
                collection.outdir is not None
            ), "Collection {dataset_id} outdir is not set"

            dataset = Dataset.fetch_by_id(dataset_id, api_key=self.api_key)
            if dataset.estimated_dataset_size is not None:
                sz_mb = int(dataset.estimated_dataset_size) // 1e6
                logger.info(f"Total {dataset_id} dataset size: {sz_mb:,} MB")

            if dry_run:
                continue

            aoi = None
            if collection.aoi_file is not None:
                with open(collection.aoi_file) as f:
                    aoi_data = json.loads(f.read())
                    aoi = aoi_data["features"]
                    assert (
                        len(aoi) == 1
                    ), "Radiant MLHub only supports one polygon filter"
                    aoi = aoi[0]
            dataset.download(
                intersects=aoi,
                datetime=datetime_str_to_value(collection.datetime),
                output_dir=collection.outdir,
                api_key=self.api_key,
            )
        return True
