import os
from datetime import datetime, timedelta

import requests


def fetch_weatherapi_forecast(latitude, longitude):

    api_key = os.getenv("WEATHER_API_KEY")

    url = "http://api.weatherapi.com/v1/forecast.json"

    params = {
        "key": api_key,
        "q": f"{latitude},{longitude}",
        "days": 2,
        "aqi": "no",
        "alerts": "no",
    }

    response = requests.get(
        url,
        params=params,
    )

    response.raise_for_status()

    return response.json()


def extract_weatherapi_current_weather(data):

    current = data["current"]

    localtime = data["location"]["localtime"]

    current_hour = localtime.split(" ")[1].split(":")[0]

    hourly_data_list = data["forecast"]["forecastday"][0]["hour"]

    hourly_data = next(
        hour
        for hour in hourly_data_list
        if hour["time"].split(" ")[1].split(":")[0] == current_hour
    )

    return {
        "temp": round(current["temp_c"], 1),
        "feels_like": round(current["feelslike_c"], 1),
        "humidity": current["humidity"],
        "wind": round(current["wind_kph"], 1),
        "rain": current.get("precip_mm", 0),
        "rain_probability": hourly_data.get("chance_of_rain", 0),
    }


def extract_weatherapi_next_12_hours(data):

    forecast_days = data["forecast"]["forecastday"]

    hourly_data = []

    for day in forecast_days:

        hourly_data.extend(day["hour"])

    localtime = data["location"]["localtime"]

    current_dt = datetime.strptime(localtime, "%Y-%m-%d %H:%M")

    cutoff_dt = current_dt + timedelta(hours=12)

    filtered = []

    for hour in hourly_data:

        forecast_dt = datetime.strptime(hour["time"], "%Y-%m-%d %H:%M")

        if current_dt <= forecast_dt <= cutoff_dt:

            filtered.append(hour)

    return filtered


def summarize_weatherapi_forecast(forecasts):

    current_date = datetime.strptime(forecasts[0]["time"], "%Y-%m-%d %H:%M").date()

    def format_time(time_string, current_date):

        dt = datetime.strptime(time_string, "%Y-%m-%d %H:%M")

        formatted_time = dt.strftime("%I:%M %p").lstrip("0")

        if dt.date() > current_date:

            formatted_time += " (Tomorrow)"

        return formatted_time

    max_temp = max(forecasts, key=lambda x: x["temp_c"])

    min_temp = min(forecasts, key=lambda x: x["temp_c"])

    max_humidity = max(forecasts, key=lambda x: x["humidity"])

    max_wind = max(forecasts, key=lambda x: x["wind_kph"])

    max_rain_prob = max(forecasts, key=lambda x: x.get("chance_of_rain", 0))

    rainy_forecasts = [f for f in forecasts if f.get("chance_of_rain", 0) >= 40]

    rain_window = None

    if rainy_forecasts:

        rain_window = {
            "start": format_time(rainy_forecasts[0]["time"], current_date),
            "end": format_time(rainy_forecasts[-1]["time"], current_date),
        }

    return {
        "max_temp": {
            "value": max_temp["temp_c"],
            "time": format_time(max_temp["time"], current_date),
        },
        "min_temp": {
            "value": min_temp["temp_c"],
            "time": format_time(min_temp["time"], current_date),
        },
        "max_humidity": {
            "value": max_humidity["humidity"],
            "time": format_time(max_humidity["time"], current_date),
        },
        "max_wind": {
            "value": round(max_wind["wind_kph"], 1),
            "time": format_time(max_wind["time"], current_date),
        },
        "max_rain_probability": {
            "value": max_rain_prob.get("chance_of_rain", 0),
            "time": format_time(max_rain_prob["time"], current_date),
        },
        "rain_window": rain_window,
    }
