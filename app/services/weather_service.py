"""
Weather processing service.

Handles:
- Current weather extraction
- Forecast grouping
- Forecast summarization
- OpenWeather normalization
"""

from datetime import datetime

from app.external.weather_client import convert_timestamp, fetch_weather_raw


def parse_datetime(value: str) -> datetime:
    """
    Parse ISO datetime string.

    Parameters
    ----------
    value : str

    Returns
    -------
    datetime
    """
    return datetime.fromisoformat(value)


def extract_current_weather(data: dict) -> dict:
    """
    Extract current weather conditions.

    Parameters
    ----------
    data : dict

    Returns
    -------
    dict
    """
    current = data["current"]

    timezone_name = data["timezone"]

    current_dt = convert_timestamp(
        current["dt"],
        timezone_name,
    )

    return {
        "datetime": current_dt.isoformat(),
        "temp": current["temp"],
        "feels_like": current["feels_like"],
        "humidity": current["humidity"],
        "wind_speed": round(
            current["wind_speed"] * 3.6,
            2,
        ),
        "rain": current.get("rain", {}).get("1h", 0),
    }


def build_hourly_entry(hour: dict, timezone_name: str) -> dict:
    """
    Build normalized hourly forecast entry.

    Parameters
    ----------
    hour : dict
    timezone_name : str

    Returns
    -------
    dict
    """
    hour_dt = convert_timestamp(
        hour["dt"],
        timezone_name,
    )

    return {
        "datetime": hour_dt.isoformat(),
        "temp": hour["temp"],
        "humidity": hour["humidity"],
        "wind_speed": round(
            hour["wind_speed"] * 3.6,
            2,
        ),
        "rain_probability": int(hour.get("pop", 0) * 100),
        "rain": hour.get("rain", {}).get("1h", 0),
        "condition": hour["weather"][0]["description"],
    }


def initialize_forecast_groups(data: dict) -> dict:
    """
    Initialize forecast containers.

    Parameters
    ----------
    data : dict

    Returns
    -------
    dict
    """
    return {
        "today": {
            "summary": data["daily"][0]["summary"],
            "hourly": [],
        },
        "tomorrow": {
            "summary": data["daily"][1]["summary"],
            "hourly": [],
        },
    }


def group_hourly_forecast(data: dict) -> dict:
    """
    Group hourly forecast by day.

    Parameters
    ----------
    data : dict

    Returns
    -------
    dict
    """
    timezone_name = data["timezone"]

    grouped = initialize_forecast_groups(data)

    current_date = convert_timestamp(
        data["current"]["dt"],
        timezone_name,
    ).date()

    tomorrow_date = current_date.fromordinal(current_date.toordinal() + 1)

    for hour in data["hourly"]:

        entry = build_hourly_entry(
            hour,
            timezone_name,
        )

        hour_date = parse_datetime(entry["datetime"]).date()

        if hour_date == current_date:
            grouped["today"]["hourly"].append(entry)

        elif hour_date == tomorrow_date:
            grouped["tomorrow"]["hourly"].append(entry)

    return grouped


def extract_rain_windows(hourly_data: list[dict]) -> list[str]:
    """
    Extract probable rain time windows.

    Parameters
    ----------
    hourly_data : list[dict]

    Returns
    -------
    list[str]
    """
    rainy_hours = []

    for hour in hourly_data:

        if hour["rain_probability"] >= 40 or hour["rain"] > 0:
            rainy_hours.append(hour)

    if not rainy_hours:
        return ["No significant rain expected"]

    return build_rain_windows(rainy_hours)


def build_rain_windows(rainy_hours: list[dict]) -> list[str]:
    """
    Merge continuous rainy hours.

    Parameters
    ----------
    rainy_hours : list[dict]

    Returns
    -------
    list[str]
    """
    windows = []

    current_window = [rainy_hours[0]]

    for current_hour, next_hour in zip(
        rainy_hours,
        rainy_hours[1:],
    ):
        current_dt = parse_datetime(current_hour["datetime"])
        next_dt = parse_datetime(next_hour["datetime"])
        diff = (next_dt - current_dt).seconds / 3600

        if diff <= 1.5:
            current_window.append(next_hour)

        else:
            windows.append(current_window)
            current_window = [next_hour]

    windows.append(current_window)

    return format_rain_windows(windows)


def format_rain_windows(windows: list[list[dict]]) -> list[str]:
    """
    Format rain windows into readable strings.

    Parameters
    ----------
    windows : list[list[dict]]

    Returns
    -------
    list[str]
    """
    formatted = []

    for window in windows:

        start = parse_datetime(window[0]["datetime"]).strftime("%I:%M %p")

        end = parse_datetime(window[-1]["datetime"]).strftime("%I:%M %p")

        formatted.append(f"{start} to {end}")

    return formatted


def summarize_rain(hourly_data: list[dict]) -> dict:
    """
    Summarize rainfall metrics.

    Parameters
    ----------
    hourly_data : list[dict]

    Returns
    -------
    dict
    """
    if not hourly_data:
        return {
            "rain_probability": 0,
            "rain_mm": 0,
        }

    max_probability = max(hour["rain_probability"] for hour in hourly_data)

    total_rain = round(
        sum(hour["rain"] for hour in hourly_data),
        2,
    )

    return {
        "rain_probability": max_probability,
        "rain_mm": total_rain,
    }


def build_day_forecast_summary(
    hourly_data: list[dict],
    summary: str,
    rain_data: dict,
    rain_windows: list[str],
) -> dict:
    """
    Build summarized day forecast.

    Parameters
    ----------
    hourly_data : list[dict]
    summary : str
    rain_data : dict
    rain_windows : list[str]

    Returns
    -------
    dict
    """
    max_temp = max(
        hourly_data,
        key=lambda x: x["temp"],
    )

    min_temp = min(
        hourly_data,
        key=lambda x: x["temp"],
    )

    max_humidity = max(
        hourly_data,
        key=lambda x: x["humidity"],
    )

    max_wind = max(
        hourly_data,
        key=lambda x: x["wind_speed"],
    )

    return {
        "summary": summary,
        "max_temp": build_metric_entry(
            max_temp,
            "temp",
        ),
        "min_temp": build_metric_entry(
            min_temp,
            "temp",
        ),
        "max_humidity": build_metric_entry(
            max_humidity,
            "humidity",
        ),
        "max_wind": build_metric_entry(
            max_wind,
            "wind_speed",
        ),
        "rain_probability": rain_data["rain_probability"],
        "rain_mm": rain_data["rain_mm"],
        "rain_windows": rain_windows,
    }


def build_metric_entry(
    record: dict,
    field: str,
) -> dict:
    """
    Build timestamped metric entry.

    Parameters
    ----------
    record : dict
    field : str

    Returns
    -------
    dict
    """
    return {
        "value": record[field],
        "time": (parse_datetime(record["datetime"]).strftime("%I:%M %p")),
    }


def extract_day3_forecast(data: dict) -> dict:
    """
    Extract simplified day-3 forecast.

    Parameters
    ----------
    data : dict

    Returns
    -------
    dict
    """
    day3 = data["daily"][2]

    return {
        "summary": day3["summary"],
        "min_temp": day3["temp"]["min"],
        "max_temp": day3["temp"]["max"],
        "humidity": day3["humidity"],
        "wind_speed": round(
            day3["wind_speed"] * 3.6,
            2,
        ),
        "rain_probability": int(day3.get("pop", 0) * 100),
        "rain": day3.get("rain", 0),
    }


def build_weather_payload(
    latitude: float,
    longitude: float,
) -> dict:
    """
    Build normalized weather payload.

    Parameters
    ----------
    latitude : float
    longitude : float

    Returns
    -------
    dict
    """
    weather_data = fetch_weather_raw(
        latitude,
        longitude,
    )

    grouped = group_hourly_forecast(weather_data)

    today_hourly = grouped["today"]["hourly"]

    tomorrow_hourly = grouped["tomorrow"]["hourly"]

    return {
        "current_weather": extract_current_weather(weather_data),
        "today_forecast": build_day_forecast_summary(
            hourly_data=today_hourly,
            summary=grouped["today"]["summary"],
            rain_data=summarize_rain(today_hourly),
            rain_windows=extract_rain_windows(today_hourly),
        ),
        "tomorrow_forecast": build_day_forecast_summary(
            hourly_data=tomorrow_hourly,
            summary=grouped["tomorrow"]["summary"],
            rain_data=summarize_rain(tomorrow_hourly),
            rain_windows=extract_rain_windows(tomorrow_hourly),
        ),
        "day3_forecast": extract_day3_forecast(weather_data),
    }
