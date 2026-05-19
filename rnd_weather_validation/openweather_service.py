import os
from datetime import datetime
from zoneinfo import ZoneInfo

import requests


def fetch_openweather_data(latitude, longitude):

    api_key = os.getenv("OPENWEATHER_API_KEY")

    url = "https://api.openweathermap.org" "/data/3.0/onecall"

    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": api_key,
        "units": "metric",
        "exclude": "minutely,alerts",
    }

    response = requests.get(
        url,
        params=params,
    )

    response.raise_for_status()
    return response.json()


def convert_timestamp(timestamp, timezone_name):

    timezone = ZoneInfo(timezone_name)
    return datetime.fromtimestamp(timestamp, timezone)


def extract_current_weather(data):

    current = data["current"]
    timezone_name = data["timezone"]

    current_dt = convert_timestamp(
        current["dt"],
        timezone_name,
    )

    return {
        "datetime": current_dt,
        "temp": current["temp"],
        "feels_like": current["feels_like"],
        "humidity": current["humidity"],
        "wind_speed": round(current["wind_speed"] * 3.6, 2),
        "rain": current.get("rain", {}).get("1h", 0),
    }


def group_hourly_forecast(data):

    timezone_name = data["timezone"]

    grouped_forecast = {
        "today": {
            "summary": data["daily"][0]["summary"],
            "hourly": [],
        },
        "tomorrow": {
            "summary": data["daily"][1]["summary"],
            "hourly": [],
        },
    }

    current_date = convert_timestamp(data["current"]["dt"], timezone_name).date()

    tomorrow_date = current_date.fromordinal(current_date.toordinal() + 1)

    for hour in data["hourly"]:

        hour_dt = convert_timestamp(hour["dt"], timezone_name)

        forecast_entry = {
            "datetime": hour_dt,
            "temp": hour["temp"],
            "humidity": hour["humidity"],
            "wind_speed": round(hour["wind_speed"] * 3.6, 2),
            "rain_probability": int(hour.get("pop", 0) * 100),
            "rain": hour.get("rain", {}).get("1h", 0),
            "condition": hour["weather"][0]["description"],
        }

        if hour_dt.date() == current_date:
            grouped_forecast["today"]["hourly"].append(forecast_entry)

        elif hour_dt.date() == tomorrow_date:
            grouped_forecast["tomorrow"]["hourly"].append(forecast_entry)

    return grouped_forecast


def extract_day3_forecast(data):

    day3 = data["daily"][2]

    return {
        "summary": day3["summary"],
        "min_temp": day3["temp"]["min"],
        "max_temp": day3["temp"]["max"],
        "humidity": day3["humidity"],
        "wind_speed": round(day3["wind_speed"] * 3.6, 2),
        "rain_probability": int(day3.get("pop", 0) * 100),
        "rain": day3.get("rain", 0),
    }
