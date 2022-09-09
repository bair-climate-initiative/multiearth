"""EarthData Provider.

https://www.earthdata.nasa.gov/
"""

from typing import Any, List

import requests

from ..config import CollectionSchema, ConfigSchema, ProviderKey
from .earthdata_providers import EARTHDATA_PROVIDERS
from .stac import STACProvider


class EarthDataProvider(STACProvider):
    """Download data and extract assets from any NASA EarthData with a STAC API."""

    _default_client_url: str = ""
    description: str = "EarthData Provider"

    def __init__(
        self,
        id: ProviderKey,
        cfg: ConfigSchema,
        collections: List[CollectionSchema],
        client_url: str = "",
        subprovider_id: str = "",
        **kwargs: Any,
    ) -> None:
        """Use one of the EarthData Providers, such as NSIDC."""
        if client_url == "" and subprovider_id == "":
            raise ValueError(
                "Must specify either client_url or provider_id for EarthDataProvider."
                f"\nProvider ids: {EARTHDATA_PROVIDERS.keys()}\n"
                "Specify using, e.g., \nprovider: \n\tname: EARTHDATA\n\tkwargs: "
                "\n\t\tprovider_id: NSIDC"
            )

        if client_url == "":
            if subprovider_id in EARTHDATA_PROVIDERS:
                client_url = EARTHDATA_PROVIDERS[subprovider_id]
            else:
                raise ValueError(
                    f"Unknown subprovider_id: {subprovider_id}, use one of "
                    + f"{', '.join(list(EARTHDATA_PROVIDERS.keys()))}"
                )

        super().__init__(id, cfg, collections, client_url)

    def check_authorization(self) -> bool:
        """Check if the provider is authorized."""
        authd = False
        # hardcoded api endpoint - should succeed if .netrc file in place
        # TODO check alaska auth and EULA agreement if using alaska subprovider
        r = requests.get("https://urs.earthdata.nasa.gov/api/users/tokens")
        try:
            r.raise_for_status()
            authd = True
        except requests.HTTPError:
            pass  # will return false
        return authd
