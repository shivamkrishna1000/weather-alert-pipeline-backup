from rnd_weather_validation.openweather_service import (
    extract_openweather_current_weather,
    extract_openweather_next_12_hours,
    fetch_openweather_forecast,
    summarize_openweather_forecast,
)
from rnd_weather_validation.weatherapi_service import (
    extract_weatherapi_current_weather,
    extract_weatherapi_next_12_hours,
    fetch_weatherapi_forecast,
    summarize_weatherapi_forecast,
)


def build_weather_comparison(latitude, longitude):

    # OpenWeather

    openweather_data = fetch_openweather_forecast(latitude, longitude)

    openweather_current = extract_openweather_current_weather(openweather_data)

    openweather_12h = extract_openweather_next_12_hours(openweather_data)

    openweather_summary = summarize_openweather_forecast(openweather_12h)

    # WeatherAPI

    weatherapi_data = fetch_weatherapi_forecast(latitude, longitude)

    weatherapi_current = extract_weatherapi_current_weather(weatherapi_data)

    weatherapi_12h = extract_weatherapi_next_12_hours(weatherapi_data)

    weatherapi_summary = summarize_weatherapi_forecast(weatherapi_12h)

    return {
        "openweather": {
            "current": openweather_current,
            "forecast": openweather_summary,
        },
        "weatherapi": {
            "current": weatherapi_current,
            "forecast": weatherapi_summary,
        },
    }
