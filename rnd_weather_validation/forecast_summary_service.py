def extract_rain_windows(hourly_data):

    rainy_hours = []

    for hour in hourly_data:

        if hour["rain_probability"] >= 40 or hour["rain"] > 0:
            rainy_hours.append(hour)

    if not rainy_hours:
        return ["No significant rain expected"]

    windows = []

    current_window = [rainy_hours[0]]

    for current_hour, next_hour in zip(rainy_hours, rainy_hours[1:]):

        hour_difference = (
            next_hour["datetime"] - current_hour["datetime"]
        ).seconds / 3600

        if hour_difference <= 1.5:
            current_window.append(next_hour)

        else:
            windows.append(current_window)
            current_window = [next_hour]

    windows.append(current_window)

    formatted_windows = []

    for window in windows:

        start_time = window[0]["datetime"].strftime("%I:%M %p").lstrip("0")

        end_time = window[-1]["datetime"].strftime("%I:%M %p").lstrip("0")

        formatted_windows.append(f"{start_time}" f" to " f"{end_time}")

    return formatted_windows


def summarize_today_rain(hourly_data):

    if not hourly_data:
        return {
            "rain_probability": 0,
            "rain_mm": 0,
        }

    max_probability = max(hour["rain_probability"] for hour in hourly_data)

    total_rain = round(sum(hour["rain"] for hour in hourly_data), 2)

    return {
        "rain_probability": (max_probability),
        "rain_mm": total_rain,
    }


def build_day_forecast_summary(
    hourly_data,
    summary,
    rain_probability,
    rain_mm,
    rain_windows,
):

    max_temp = max(hourly_data, key=lambda x: x["temp"])

    min_temp = min(hourly_data, key=lambda x: x["temp"])

    max_humidity = max(hourly_data, key=lambda x: x["humidity"])

    max_wind = max(hourly_data, key=lambda x: (x["wind_speed"]))

    return {
        "summary": summary,
        "max_temp": {
            "value": (max_temp["temp"]),
            "time": (max_temp["datetime"].strftime("%I:%M %p").lstrip("0")),
        },
        "min_temp": {
            "value": (min_temp["temp"]),
            "time": (min_temp["datetime"].strftime("%I:%M %p").lstrip("0")),
        },
        "max_humidity": {
            "value": (max_humidity["humidity"]),
            "time": (max_humidity["datetime"].strftime("%I:%M %p").lstrip("0")),
        },
        "max_wind": {
            "value": (max_wind["wind_speed"]),
            "time": (max_wind["datetime"].strftime("%I:%M %p").lstrip("0")),
        },
        "rain_probability": (rain_probability),
        "rain_mm": (rain_mm),
        "rain_windows": (rain_windows),
    }
