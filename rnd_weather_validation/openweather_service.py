import os
from datetime import datetime, timedelta

import requests


def fetch_openweather_forecast(latitude, longitude):
    api_key = os.getenv("OPENWEATHER_API_KEY")

    url = "https://api.openweathermap.org/data/2.5/forecast"

    params = {
        "lat": latitude,
        "lon": longitude,
        "units": "metric",
        "appid": api_key,
    }

    response = requests.get(url, params=params)

    response.raise_for_status()

    return response.json()


def extract_openweather_next_12_hours(data):

    forecasts = data["list"]

    timezone_offset = data["city"]["timezone"]

    now_utc = datetime.utcnow()

    cutoff_utc = now_utc + timedelta(hours=12)

    filtered = []

    for item in forecasts:

        forecast_utc = datetime.utcfromtimestamp(item["dt"])

        if now_utc <= forecast_utc <= cutoff_utc:

            item["timezone_offset"] = timezone_offset

            filtered.append(item)

    return filtered


def summarize_openweather_forecast(forecasts):

    timezone_offset = forecasts[0]["timezone_offset"]

    current_date = (
        datetime.utcfromtimestamp(forecasts[0]["dt"])
        + timedelta(seconds=timezone_offset)
    ).date()

    def format_time(
        timestamp,
        current_date,
        timezone_offset,
    ):

        local_dt = datetime.utcfromtimestamp(timestamp) + timedelta(
            seconds=timezone_offset
        )

        formatted_time = local_dt.strftime("%I:%M %p").lstrip("0")

        if local_dt.date() > current_date:

            formatted_time += " (Tomorrow)"

        return formatted_time

    max_temp = max(forecasts, key=lambda x: x["main"]["temp_max"])

    min_temp = min(forecasts, key=lambda x: x["main"]["temp_min"])

    max_humidity = max(forecasts, key=lambda x: x["main"]["humidity"])

    max_wind = max(forecasts, key=lambda x: x["wind"]["speed"])

    max_rain_prob = max(forecasts, key=lambda x: x.get("pop", 0))

    rainy_forecasts = [f for f in forecasts if f.get("pop", 0) >= 0.4]

    rain_window = None

    if rainy_forecasts:

        rain_window = {
            "start": format_time(
                rainy_forecasts[0]["dt"], current_date, timezone_offset
            ),
            "end": format_time(
                rainy_forecasts[-1]["dt"], current_date, timezone_offset
            ),
        }

    return {
        "max_temp": {
            "value": max_temp["main"]["temp_max"],
            "time": format_time(max_temp["dt"], current_date, timezone_offset),
        },
        "min_temp": {
            "value": min_temp["main"]["temp_min"],
            "time": format_time(min_temp["dt"], current_date, timezone_offset),
        },
        "max_humidity": {
            "value": max_humidity["main"]["humidity"],
            "time": format_time(max_humidity["dt"], current_date, timezone_offset),
        },
        "max_wind": {
            "value": round(max_wind["wind"]["speed"] * 3.6, 1),
            "time": format_time(max_wind["dt"], current_date, timezone_offset),
        },
        "max_rain_probability": {
            "value": round(max_rain_prob.get("pop", 0) * 100),
            "time": format_time(max_rain_prob["dt"], current_date, timezone_offset),
        },
        "rain_window": rain_window,
    }


def extract_openweather_current_weather(data):

    first_forecast = data["list"][0]

    rain_data = first_forecast.get("rain", {})

    rain_mm = rain_data.get("3h", 0)

    return {
        "temp": round(first_forecast["main"]["temp"], 1),
        "feels_like": round(first_forecast["main"]["feels_like"], 1),
        "humidity": first_forecast["main"]["humidity"],
        "wind": round(first_forecast["wind"]["speed"] * 3.6, 1),
        "rain": rain_mm,
        "rain_probability": round(first_forecast.get("pop", 0) * 100),
    }
