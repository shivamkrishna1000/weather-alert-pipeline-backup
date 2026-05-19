import os
import sys

from app.config import load_environment
from app.database import get_connection
from rnd_weather_validation.config import LOCATION_CONFIGS
from rnd_weather_validation.database import create_rnd_tables, insert_weather_snapshot
from rnd_weather_validation.forecast_summary_service import (
    build_day_forecast_summary,
    extract_rain_windows,
    summarize_today_rain,
)
from rnd_weather_validation.formatter import build_weather_report
from rnd_weather_validation.openweather_service import (
    extract_current_weather,
    extract_day3_forecast,
    fetch_openweather_data,
    group_hourly_forecast,
)
from rnd_weather_validation.storage_service import serialize_weather_data
from rnd_weather_validation.wati_service import (
    build_template_parameters,
    send_template_message,
)


def build_weather_payload(location):

    weather_data = fetch_openweather_data(location["latitude"], location["longitude"])
    current_weather = extract_current_weather(weather_data)
    grouped_forecast = group_hourly_forecast(weather_data)
    day3_forecast = extract_day3_forecast(weather_data)
    today_rain_windows = extract_rain_windows(grouped_forecast["today"]["hourly"])
    tomorrow_rain_windows = extract_rain_windows(grouped_forecast["tomorrow"]["hourly"])
    today_rain_summary = summarize_today_rain(grouped_forecast["today"]["hourly"])
    tomorrow_rain_summary = {
        "rain_probability": int(weather_data["daily"][1]["pop"] * 100),
        "rain_mm": weather_data["daily"][1].get("rain", 0),
    }

    today_forecast_summary = build_day_forecast_summary(
        hourly_data=grouped_forecast["today"]["hourly"],
        summary=grouped_forecast["today"]["summary"],
        rain_probability=today_rain_summary["rain_probability"],
        rain_mm=today_rain_summary["rain_mm"],
        rain_windows=today_rain_windows,
    )

    tomorrow_forecast_summary = build_day_forecast_summary(
        hourly_data=grouped_forecast["tomorrow"]["hourly"],
        summary=grouped_forecast["tomorrow"]["summary"],
        rain_probability=tomorrow_rain_summary["rain_probability"],
        rain_mm=tomorrow_rain_summary["rain_mm"],
        rain_windows=tomorrow_rain_windows,
    )

    weather_report = build_weather_report(
        location_name=location["name"],
        current_weather=current_weather,
        today_forecast=today_forecast_summary,
        tomorrow_forecast=tomorrow_forecast_summary,
        day3_forecast=day3_forecast,
    )

    template_parameters = build_template_parameters(
        location_name=location["name"],
        current_weather=current_weather,
        today_forecast=today_forecast_summary,
        tomorrow_forecast=tomorrow_forecast_summary,
        day3_forecast=day3_forecast,
    )

    serialized_current_weather = serialize_weather_data(current_weather)
    serialized_today_forecast = serialize_weather_data(today_forecast_summary)
    serialized_tomorrow_forecast = serialize_weather_data(tomorrow_forecast_summary)
    serialized_day3_forecast = serialize_weather_data(day3_forecast)

    return {
        "weather_report": weather_report,
        "template_parameters": template_parameters,
        "serialized_current_weather": serialized_current_weather,
        "serialized_today_forecast": serialized_today_forecast,
        "serialized_tomorrow_forecast": serialized_tomorrow_forecast,
        "serialized_day3_forecast": serialized_day3_forecast,
    }


def run_hourly_pipeline():

    connection = get_connection(os.getenv("DATABASE_URL"))
    create_rnd_tables(connection)

    for location in LOCATION_CONFIGS:

        payload = build_weather_payload(location)

        print(f"\n========== " f"{location['name']} " f"==========\n")

        print(payload["weather_report"])

        insert_weather_snapshot(
            connection=connection,
            location_name=location["name"],
            current_weather=payload["serialized_current_weather"],
            today_forecast=payload["serialized_today_forecast"],
            tomorrow_forecast=payload["serialized_tomorrow_forecast"],
            day3_forecast=payload["serialized_day3_forecast"],
            weather_report=payload["weather_report"],
        )

        print("\nWeather snapshot " "stored successfully.\n")

    connection.close()


def run_daily_pipeline():

    for location in LOCATION_CONFIGS:

        payload = build_weather_payload(location)

        print(f"\n========== " f"{location['name']} " f"==========\n")

        print(payload["weather_report"])

        for recipient in location["recipients"]:

            send_template_message(
                base_url=os.getenv("RND_WATI_API_URL"),
                api_key=os.getenv("RND_WATI_API_KEY"),
                template_name=os.getenv("RND_WATI_TEMPLATE_NAME"),
                phone_number=recipient,
                parameters=payload["template_parameters"],
            )

            print(f"Message sent " f"to {recipient}")


def main():

    load_environment()

    if len(sys.argv) < 2:

        raise ValueError("Pipeline type missing. " "Use 'hourly' " "or 'daily'.")

    pipeline_type = sys.argv[1].strip().lower()

    if pipeline_type == "hourly":
        run_hourly_pipeline()

    elif pipeline_type == "daily":
        run_daily_pipeline()

    else:
        raise ValueError("Invalid pipeline type. " "Use 'hourly' " "or 'daily'.")


if __name__ == "__main__":

    main()
