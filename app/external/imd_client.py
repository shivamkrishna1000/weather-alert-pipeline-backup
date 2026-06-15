"""
IMD API client.

Handles:
- JWT token generation
- JWT token caching
- Automatic token refresh
- District warning retrieval
"""

import time

import requests

from app.config import get_imd_api_key, get_imd_email, get_imd_password

# In-memory token cache
_access_token = None
_expiry_time = 0


def get_valid_access_token() -> str:
    """
    Retrieve a valid IMD JWT access token.

    Returns a cached token if it is still valid,
    otherwise generates a new token using the
    IMD authentication endpoint.

    Returns
    -------
    str
        Valid JWT access token.

    Notes
    -----
    - Uses in-memory caching.
    - Automatically refreshes expired tokens.
    - Refreshes slightly before actual expiry
      to avoid edge timing issues.
    """
    global _access_token, _expiry_time

    if _access_token and time.time() < _expiry_time:
        return _access_token

    return refresh_access_token()


def refresh_access_token() -> str:
    """
    Generate a new IMD JWT access token.

    Calls the IMD authentication endpoint using
    configured credentials and updates the
    in-memory token cache.

    Returns
    -------
    str
        Newly generated JWT access token.

    Raises
    ------
    RuntimeError
        If authentication fails or response
        validation fails.
    """
    global _access_token, _expiry_time

    url = "https://api.imd.gov.in/api/oauth/token.php"

    payload = {
        "email": get_imd_email(),
        "password": get_imd_password(),
    }

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=15,
        )

        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        raise RuntimeError("IMD token generation failed") from e

    try:
        data = response.json()

    except ValueError as e:
        raise RuntimeError("Invalid JSON from IMD token endpoint") from e

    token = data.get("access_token")

    if not token:
        raise RuntimeError("IMD token missing in response")

    expires_in = data.get(
        "expires_in",
        3600,
    )

    _access_token = token

    # Refresh slightly before expiry
    _expiry_time = time.time() + expires_in - 60

    return _access_token


def fetch_district_warnings() -> list[dict]:
    """
    Fetch district warning dataset from IMD.

    Uses a valid JWT token and API key to
    retrieve the latest district warning
    information.

    Returns
    -------
    list[dict]
        Raw district warning records returned
        by the IMD API.

    Raises
    ------
    RuntimeError
        If the request fails, response JSON
        is invalid, or payload structure
        is unexpected.
    """
    token = get_valid_access_token()

    headers = {
        "X-API-KEY": get_imd_api_key(),
        "Authorization": f"Bearer {token}",
    }

    url = "https://api.imd.gov.in/api/v1/districtwarning"

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=30,
        )

        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        raise RuntimeError("IMD district warning API request failed") from e

    try:
        data = response.json()

    except ValueError as e:
        raise RuntimeError("Invalid JSON from IMD district warning API") from e

    return validate_district_warning_response(data)


def validate_district_warning_response(data: object) -> list[dict]:
    """
    Validate district warning API response.

    Parameters
    ----------
    data : object
        Parsed JSON response from IMD.

    Returns
    -------
    list[dict]
        Validated district warning records.

    Raises
    ------
    RuntimeError
        If payload structure is invalid.
    """
    if not isinstance(data, list):
        raise RuntimeError("Unexpected IMD district warning payload")

    for record in data:

        if not isinstance(record, dict):
            raise RuntimeError("Invalid district warning record")

    return data
