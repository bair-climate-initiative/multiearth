"""EarthData Provider.

https://www.earthdata.nasa.gov/
"""

import requests

from .stac import STACProvider
from .earthdata_providers import EARTHDATA_PROVIDERS


class EarthDataProvider(STACProvider):
    """Download data and extract assets from any NASA EarthData with a STAC API."""

    _default_client_url: str = ""
    _description: str = "EarthData Provider"

    def __init__(self, client_url: str = "", provider_id: str = "") -> None:
        """Use one of the EarthData Providers, such as NSIDC."""
        if client_url == "" and provider_id == "":
            raise ValueError(
                "Must specify either client_url or provider_id for EarthDataProvider."
                + f"\nProvider ids: {EARTHDATA_PROVIDERS.keys()}\n"
                + "Specify using, e.g., \nprovider: \n\tname: EARTHDATA\n\tkwargs: "
                + "\n\t\tprovider_id: NSIDC"
            )
        if client_url == "":
            if provider_id in EARTHDATA_PROVIDERS:
                client_url = EARTHDATA_PROVIDERS[provider_id]
            else:
                raise ValueError(
                    f"Unknown provider_id: {provider_id}, use one of "
                    + f"{', '.join(list(EARTHDATA_PROVIDERS.keys()))}"
                )
        super().__init__(client_url)

    def check_authorization(self) -> bool:
        """Check if the provider is authorized."""
        authd = False
        # hardcoded api endpoint - should succeed if .netrc file in place
        r = requests.get("https://urs.earthdata.nasa.gov/api/users/tokens")
        try:
            r.raise_for_status()
            authd = True
        except requests.HTTPError:
            pass  # will return false
        return authd
