from unittest.mock import MagicMock, patch

import requests

from app.constants import ZOHO_FIELDS
from app.services.advisory_service import generate_advisories
from app.services.cluster_service import build_cluster_key, build_distance_clusters
from app.services.delivery_service import (
    group_advisories_by_farmer,
    split_advisory_sections,
)
from app.services.geocode_service import should_retry
from app.services.greenhouse_service import process_greenhouse_records
from app.services.wati_service import send_whatsapp_message
from app.services.weather_service import build_weather_payload

# ------------------ GREENHOUSE SERVICE ------------------


def test_process_greenhouse_records_split():
    records = [
        {
            ZOHO_FIELDS["status"]: "2. FS taken over and being used",
            ZOHO_FIELDS["latitude"]: 17.1,
            ZOHO_FIELDS["longitude"]: 78.1,
            ZOHO_FIELDS["id"]: "1",
        },
        {
            ZOHO_FIELDS["status"]: "2. FS taken over and being used",
            ZOHO_FIELDS["latitude"]: None,
            ZOHO_FIELDS["longitude"]: None,
            ZOHO_FIELDS["id"]: "2",
        },
    ]

    with_loc, without_loc = process_greenhouse_records(records)

    assert len(with_loc) == 1
    assert len(without_loc) == 1


# ------------------ GEOCODE SERVICE ------------------


def test_should_retry_logic():
    assert should_retry(0) is True
    assert should_retry(2) is True
    assert should_retry(3) is False


# ------------------ WEATHER SERVICE ------------------


def test_build_weather_payload_calls_fetch():

    with patch("app.services.weather_service.fetch_weather_raw") as mock_fetch, patch(
        "app.services.weather_service.extract_current_weather",
        return_value={"temp": 30},
    ), patch(
        "app.services.weather_service.group_hourly_forecast",
        return_value={
            "today": {
                "summary": "Sunny",
                "hourly": [
                    {
                        "temp": 30,
                        "humidity": 50,
                        "wind_speed": 10,
                        "rain": 0,
                        "rain_probability": 0,
                        "datetime": "2026-01-01T10:00:00",
                    }
                ],
            },
            "tomorrow": {
                "summary": "Cloudy",
                "hourly": [
                    {
                        "temp": 28,
                        "humidity": 60,
                        "wind_speed": 12,
                        "rain": 0,
                        "rain_probability": 10,
                        "datetime": "2026-01-02T10:00:00",
                    }
                ],
            },
        },
    ), patch(
        "app.services.weather_service.extract_day3_forecast",
        return_value={"summary": "Dry"},
    ):

        mock_fetch.return_value = {}

        result = build_weather_payload(1, 2)

        mock_fetch.assert_called_once_with(1, 2)

        assert "current_weather" in result
        assert "today_forecast" in result
        assert "tomorrow_forecast" in result
        assert "day3_forecast" in result


def test_summarize_rain_empty():

    from app.services.weather_service import summarize_rain

    result = summarize_rain([])

    assert result == {
        "rain_probability": 0,
        "rain_mm": 0,
    }


def test_extract_rain_windows_no_rain():

    from app.services.weather_service import extract_rain_windows

    result = extract_rain_windows([])

    assert result == ["No significant rain expected"]


def test_build_metric_entry():

    from app.services.weather_service import build_metric_entry

    result = build_metric_entry(
        {
            "temp": 35,
            "datetime": "2026-01-01T15:00:00",
        },
        "temp",
    )

    assert result["value"] == 35
    assert result["time"] == "03:00 PM"


def test_extract_day3_forecast():

    from app.services.weather_service import extract_day3_forecast

    result = extract_day3_forecast(
        {
            "daily": [
                {},
                {},
                {
                    "summary": "Dry",
                    "temp": {
                        "min": 20,
                        "max": 35,
                    },
                    "humidity": 60,
                    "wind_speed": 5,
                    "pop": 0.5,
                    "rain": 3,
                },
            ]
        }
    )

    assert result["summary"] == "Dry"
    assert result["max_temp"] == 35
    assert result["rain_probability"] == 50


def test_extract_current_weather():

    from app.services.weather_service import extract_current_weather

    with patch("app.services.weather_service.convert_timestamp") as mock_convert:

        from datetime import datetime

        mock_convert.return_value = datetime.fromisoformat("2026-01-01T10:00:00")

        result = extract_current_weather(
            {
                "timezone": "Asia/Kolkata",
                "current": {
                    "dt": 123,
                    "temp": 30,
                    "feels_like": 34,
                    "humidity": 80,
                    "wind_speed": 5,
                    "rain": {"1h": 2},
                },
            }
        )

        assert result["temp"] == 30
        assert result["wind_speed"] == 18.0
        assert result["rain"] == 2


def test_build_rain_windows_multiple_windows():

    from app.services.weather_service import build_rain_windows

    rainy_hours = [
        {"datetime": "2026-01-01T10:00:00"},
        {"datetime": "2026-01-01T11:00:00"},
        {"datetime": "2026-01-01T15:00:00"},
    ]

    result = build_rain_windows(rainy_hours)

    assert len(result) == 2


def test_group_hourly_forecast():

    from datetime import datetime

    from app.services.weather_service import group_hourly_forecast

    with patch("app.services.weather_service.convert_timestamp") as mock_convert:

        mock_convert.side_effect = [
            datetime.fromisoformat("2026-01-01T08:00:00"),
            datetime.fromisoformat("2026-01-01T10:00:00"),
            datetime.fromisoformat("2026-01-02T10:00:00"),
        ]

        result = group_hourly_forecast(
            {
                "timezone": "Asia/Kolkata",
                "current": {"dt": 1},
                "daily": [
                    {"summary": "Sunny"},
                    {"summary": "Cloudy"},
                ],
                "hourly": [
                    {
                        "dt": 2,
                        "temp": 30,
                        "humidity": 50,
                        "wind_speed": 5,
                        "weather": [{"description": "sunny"}],
                    },
                    {
                        "dt": 3,
                        "temp": 25,
                        "humidity": 60,
                        "wind_speed": 5,
                        "weather": [{"description": "cloudy"}],
                    },
                ],
            }
        )

        assert len(result["today"]["hourly"]) == 1

        assert len(result["tomorrow"]["hourly"]) == 1


# ------------------ CLUSTER SERVICE ------------------


def test_build_distance_clusters_basic():
    records = [
        {"latitude": 10.0, "longitude": 20.0},
        {"latitude": 10.001, "longitude": 20.001},
    ]

    result = build_distance_clusters(records)

    assert len(result) == 1
    assert "cluster_key" in result[0]


def test_build_cluster_key_taluk_mode():
    record = {
        "district": "Bangalore-East",
        "taluk": "North-1",
        "village": "X",
    }

    with patch("app.services.cluster_service.get_cluster_mode", return_value="taluk"):
        result = build_cluster_key(record)

    assert result == "taluk_Bangalore_North"


# ------------------ WATI SERVICE ------------------


SECTIONS = {
    "greenhouse": "GH1",
    "current": "Current alert",
    "today": "Today alert",
    "tomorrow": "Tomorrow alert",
    "day3": "Day3 alert",
}


@patch("app.services.wati_service.is_debug_mode", return_value=True)
def test_send_whatsapp_debug_mode(mock_debug):
    result = send_whatsapp_message("919999999999", "Ravi", "Test message")

    assert result is False


@patch("app.services.wati_service.is_debug_mode", return_value=False)
@patch("app.services.wati_service.get_wati_template_name", return_value="template")
@patch("app.services.wati_service.get_wati_api_token", return_value="token")
@patch("app.services.wati_service.get_wati_base_url", return_value="http://test")
@patch("app.services.wati_service.requests.post")
def test_send_whatsapp_success(
    mock_post, mock_url, mock_token, mock_template, mock_debug
):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": True}
    mock_response.raise_for_status.return_value = None

    mock_post.return_value = mock_response

    result = send_whatsapp_message("919999999999", "Ravi", SECTIONS)

    assert result is True


@patch("app.services.wati_service.is_debug_mode", return_value=False)
@patch("app.services.wati_service.get_wati_template_name", return_value="template")
@patch("app.services.wati_service.get_wati_api_token", return_value="token")
@patch("app.services.wati_service.get_wati_base_url", return_value="http://test")
@patch(
    "app.services.wati_service.requests.post",
    side_effect=requests.exceptions.RequestException("fail"),
)
def test_send_whatsapp_api_failure(
    mock_post, mock_url, mock_token, mock_template, mock_debug
):
    result = send_whatsapp_message("919999999999", "Ravi", SECTIONS)

    assert result is False


@patch("app.services.wati_service.is_debug_mode", return_value=False)
@patch("app.services.wati_service.get_wati_template_name", return_value="template")
@patch("app.services.wati_service.get_wati_api_token", return_value="token")
@patch("app.services.wati_service.get_wati_base_url", return_value="http://test")
@patch("app.services.wati_service.requests.post")
def test_send_whatsapp_invalid_json(
    mock_post, mock_url, mock_token, mock_template, mock_debug
):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError("bad json")
    mock_response.raise_for_status.return_value = None

    mock_post.return_value = mock_response

    result = send_whatsapp_message("919999999999", "Ravi", SECTIONS)

    assert result is False


@patch("app.services.wati_service.is_debug_mode", return_value=False)
@patch("app.services.wati_service.get_wati_template_name", return_value="template")
@patch("app.services.wati_service.get_wati_api_token", return_value="token")
@patch("app.services.wati_service.get_wati_base_url", return_value="http://test")
@patch("app.services.wati_service.requests.post")
def test_send_whatsapp_result_false(
    mock_post, mock_url, mock_token, mock_template, mock_debug
):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": False}
    mock_response.raise_for_status.return_value = None

    mock_post.return_value = mock_response

    result = send_whatsapp_message("919999999999", "Ravi", SECTIONS)

    assert result is False


# ------------------ DELIVERY SERVICE ------------------


def test_group_advisories():
    records = [
        {
            "phone": "999",
            "farmer_name": "Ravi",
            "greenhouse_name": "GH1",
            "advisory": "Rain alert",
            "id": 1,
        },
        {
            "phone": "999",
            "farmer_name": "Ravi",
            "greenhouse_name": "GH1",
            "advisory": "Wind alert",
            "id": 2,
        },
    ]

    result = group_advisories_by_farmer(records)

    assert "999" in result
    assert len(result["999"]["advisories"]) == 2


def test_group_advisories_skip_invalid():
    records = [
        {
            "phone": None,
            "farmer_name": "Ravi",
            "greenhouse_name": "GH1",
            "advisory": "Rain alert",
            "id": 1,
        }
    ]

    result = group_advisories_by_farmer(records)

    assert result == {}


def test_split_advisory_sections():

    advisory = {
        "greenhouse": "GH1",
        "current": "Current alert",
        "today": "Today alert",
        "tomorrow": "Tomorrow alert",
        "day3": "Day3 alert",
    }

    result = split_advisory_sections(
        "GH1",
        [advisory],
    )

    assert result["greenhouse"] == "GH1"
    assert result["current"] == "Current alert"
    assert result["today"] == "Today alert"
    assert result["tomorrow"] == "Tomorrow alert"
    assert result["day3"] == "Day3 alert"


# ------------------ ADVISORY SERVICE ------------------


def build_advisory_payload(
    rain_probability=0,
    rain_mm=0,
    max_temp=30,
    humidity=50,
    wind=10,
):
    return {
        "current_weather": {
            "temp": 30,
            "feels_like": 30,
            "humidity": 50,
            "wind_speed": 5,
            "rain": 0,
        },
        "today_forecast": {
            "summary": "Test",
            "max_temp": {
                "value": max_temp,
                "time": "12:00 PM",
            },
            "min_temp": {
                "value": 20,
                "time": "06:00 AM",
            },
            "max_humidity": {
                "value": humidity,
                "time": "08:00 AM",
            },
            "max_wind": {
                "value": wind,
                "time": "03:00 PM",
            },
            "rain_probability": rain_probability,
            "rain_mm": rain_mm,
            "rain_windows": ["06:00 PM to 08:00 PM"],
        },
        "tomorrow_forecast": {
            "summary": "Test",
            "max_temp": {
                "value": 30,
                "time": "12:00 PM",
            },
            "min_temp": {
                "value": 20,
                "time": "06:00 AM",
            },
            "max_humidity": {
                "value": 50,
                "time": "08:00 AM",
            },
            "max_wind": {
                "value": 10,
                "time": "03:00 PM",
            },
            "rain_probability": 0,
            "rain_mm": 0,
            "rain_windows": ["No significant rain expected"],
        },
        "day3_forecast": {
            "summary": "Dry",
            "max_temp": 30,
            "min_temp": 20,
            "humidity": 50,
            "wind_speed": 10,
            "rain_probability": 10,
            "rain": 0,
        },
    }


def test_heavy_rain_advisory_triggers():

    payload = build_advisory_payload(
        rain_probability=90,
        rain_mm=10,
    )

    result = generate_advisories(payload)

    assert "Heavy rain expected today" in result["today"]


def test_wind_advisory_triggers():

    payload = build_advisory_payload(
        wind=30,
    )

    result = generate_advisories(payload)

    assert "Strong winds expected today" in result["today"]


def test_humidity_advisory_triggers():

    payload = build_advisory_payload(
        humidity=90,
    )

    result = generate_advisories(payload)

    assert "High humidity expected today" in result["today"]


def test_rain_suppresses_moderate_rain():

    payload = build_advisory_payload(
        rain_probability=90,
        rain_mm=10,
    )

    result = generate_advisories(payload)

    assert "Heavy rain expected today" in result["today"]
    assert "Moderate rainfall possible today" not in result["today"]
