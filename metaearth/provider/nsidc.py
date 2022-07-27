"""NSIDC Provider.

https://nsidc.org/
"""

import requests

from .base import STACProvider


class NSIDCProvider(STACProvider):
    """Download data and extract assets from NSIDC."""

    _default_client_url: str = "https://cmr.earthdata.nasa.gov/stac/NSIDC_ECS"
    _description: str = "NSIDC Provider (nsidc.org)"

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
