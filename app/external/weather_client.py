"""
OpenWeather API client.

Handles:
- Forecast fetching from OpenWeather One Call API
- Timestamp conversion
- Basic response validation
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import requests

from app.config import get_openweather_api_key


def fetch_weather_raw(latitude: float, longitude: float) -> dict:
    """
    Fetch raw forecast data from OpenWeather.

    Parameters
    ----------
    latitude : float
    longitude : float

    Returns
    -------
    dict
        Raw OpenWeather API response.

    Raises
    ------
    RuntimeError
        If API request or response validation fails.
    """
    api_key = get_openweather_api_key()

    url = "https://api.openweathermap.org/data/3.0/onecall"

    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": api_key,
        "units": "metric",
        "exclude": "minutely,alerts",
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=15,
        )

        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        raise RuntimeError("OpenWeather API request failed") from e

    try:
        data = response.json()

    except ValueError as e:
        raise RuntimeError("Invalid JSON from OpenWeather") from e

    validate_weather_response(data)

    return data


def validate_weather_response(data: dict) -> None:
    """
    Validate required OpenWeather fields.

    Parameters
    ----------
    data : dict

    Raises
    ------
    RuntimeError
        If required fields are missing.
    """
    required = [
        "current",
        "hourly",
        "daily",
        "timezone",
    ]

    for field in required:
        if field not in data:
            raise RuntimeError(f"Missing OpenWeather field: {field}")


def convert_timestamp(
    timestamp: int,
    timezone_name: str,
) -> datetime:
    """
    Convert UNIX timestamp into timezone-aware datetime.

    Parameters
    ----------
    timestamp : int
    timezone_name : str

    Returns
    -------
    datetime
    """
    timezone = ZoneInfo(timezone_name)

    return datetime.fromtimestamp(
        timestamp,
        timezone,
    )
