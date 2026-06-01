from unittest.mock import MagicMock, patch

import pytest
import requests

from app.external import zoho_client
from app.external.maps_client import geocode_address
from app.external.weather_client import fetch_weather_raw
from app.external.zoho_client import fetch_all_greenhouse_data, refresh_access_token

# ------------------ MAPS CLIENT ------------------


@patch("app.external.maps_client.get_google_maps_api_key", return_value="fake-key")
@patch("app.external.maps_client.requests.get")
def test_geocode_address_success(mock_get, mock_key):
    mock_get.return_value.status_code = 200
    mock_get.return_value.raise_for_status = MagicMock()
    mock_get.return_value.json.return_value = {
        "status": "OK",
        "results": [{"geometry": {"location": {"lat": 10.0, "lng": 20.0}}}],
    }

    lat, lon = geocode_address("test")

    assert lat == 10.0
    assert lon == 20.0


@patch("app.external.maps_client.requests.get")
def test_geocode_address_failure(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"status": "ZERO_RESULTS"}

    with pytest.raises(ValueError):
        geocode_address("bad")


@patch("app.external.maps_client.get_google_maps_api_key", return_value="fake-key")
@patch("app.external.maps_client.requests.get")
def test_geocode_address_request_exception(mock_get, mock_key):

    mock_get.side_effect = requests.exceptions.RequestException("network error")

    with pytest.raises(RuntimeError):
        geocode_address("test")


# ------------------ ZOHO CLIENT ------------------


class DummyResponse:
    def __init__(self, data):
        self._data = data
        self.text = "x"

    def json(self):
        return self._data


def test_get_valid_access_token_cached(monkeypatch):

    zoho_client._access_token = "cached"
    zoho_client._expiry_time = 9999999999  # future

    token = zoho_client.get_valid_access_token()

    assert token == "cached"


@patch("app.external.zoho_client.get_zoho_client_id", return_value="id")
@patch("app.external.zoho_client.get_zoho_client_secret", return_value="secret")
@patch("app.external.zoho_client.get_zoho_refresh_token", return_value="refresh")
@patch("app.external.zoho_client.requests.post")
def test_refresh_access_token(mock_post, mock_refresh, mock_secret, mock_id):

    mock_post.return_value.json.return_value = {
        "access_token": "new_token",
        "expires_in": 3600,
    }
    mock_post.return_value.raise_for_status = lambda: None

    token = refresh_access_token()

    assert token == "new_token"


@patch("app.external.zoho_client.requests.post")
@patch("app.external.zoho_client.get_valid_access_token", return_value="token")
@patch("app.external.zoho_client.get_last_sync_time", return_value=None)
def test_fetch_all_greenhouse_data_multiple_pages(mock_sync, mock_token, mock_post):

    response1 = MagicMock()
    response1.status_code = 200
    response1.text = "x"
    response1.json.return_value = {
        "data": [{"id": "1"}],
        "info": {"more_records": True},
    }

    response2 = MagicMock()
    response2.status_code = 200
    response2.text = "x"
    response2.json.return_value = {
        "data": [],
        "info": {"more_records": False},
    }

    mock_post.side_effect = [response1, response2]

    result = fetch_all_greenhouse_data(connection=None)

    assert result == [{"id": "1"}]


@patch("app.external.zoho_client.requests.post")
@patch("app.external.zoho_client.get_valid_access_token", return_value="fake-token")
@patch("app.external.zoho_client.get_last_sync_time", return_value=None)
def test_fetch_all_greenhouse_data_empty_response(mock_sync, mock_token, mock_post):
    response = MagicMock()
    response.status_code = 204
    response.text = ""

    mock_post.return_value = response

    result = fetch_all_greenhouse_data(connection=None)

    assert result == []


# ------------------ WEATHER CLIENT ------------------


def test_fetch_weather_success():

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "current": {},
        "hourly": [],
        "daily": [],
        "timezone": "Asia/Kolkata",
    }
    mock_response.raise_for_status.return_value = None

    with patch(
        "app.external.weather_client.requests.get", return_value=mock_response
    ), patch("app.external.weather_client.get_openweather_api_key", return_value="key"):

        result = fetch_weather_raw(1, 2)

        assert "current" in result


def test_fetch_weather_request_failure():

    with patch(
        "app.external.weather_client.requests.get",
        side_effect=requests.exceptions.RequestException,
    ), patch("app.external.weather_client.get_openweather_api_key", return_value="key"):

        with pytest.raises(RuntimeError):
            fetch_weather_raw(1, 2)


def test_fetch_weather_invalid_json():

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = ValueError()

    with patch(
        "app.external.weather_client.requests.get", return_value=mock_response
    ), patch("app.external.weather_client.get_openweather_api_key", return_value="key"):

        with pytest.raises(RuntimeError):
            fetch_weather_raw(1, 2)


def test_fetch_weather_missing_current():

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {}

    with patch(
        "app.external.weather_client.requests.get", return_value=mock_response
    ), patch("app.external.weather_client.get_openweather_api_key", return_value="key"):

        with pytest.raises(RuntimeError):
            fetch_weather_raw(1, 2)
