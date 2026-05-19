def format_current_weather(current_weather):

    current_time = (
        current_weather["datetime"].strftime("%d %B %Y\n" "%I:%M %p").lstrip("0")
    )

    return (
        f"CURRENT WEATHER\n\n"
        f"Date & Time: "
        f"{current_time}\n\n"
        f"Temperature: "
        f"{current_weather['temp']}°C\n"
        f"Feels Like: "
        f"{current_weather['feels_like']}°C\n"
        f"Humidity: "
        f"{current_weather['humidity']}%\n"
        f"Wind Speed: "
        f"{current_weather['wind_speed']} km/h\n"
        f"Rainfall: "
        f"{current_weather['rain']} mm"
    )


def format_day_forecast(title, forecast):

    rain_windows = "\n".join([f"• {window}" for window in forecast["rain_windows"]])

    return (
        f"{title}\n\n"
        f"Summary: "
        f"{forecast['summary']}\n\n"
        f"Maximum Temperature: "
        f"{forecast['max_temp']['value']}°C "
        f"at "
        f"{forecast['max_temp']['time']}\n"
        f"Minimum Temperature: "
        f"{forecast['min_temp']['value']}°C "
        f"at "
        f"{forecast['min_temp']['time']}\n"
        f"Maximum Humidity: "
        f"{forecast['max_humidity']['value']}% "
        f"at "
        f"{forecast['max_humidity']['time']}\n"
        f"Maximum Wind Speed: "
        f"{forecast['max_wind']['value']} km/h "
        f"at "
        f"{forecast['max_wind']['time']}\n\n"
        f"Rain Probability: "
        f"{forecast['rain_probability']}%\n"
        f"Expected Rainfall: "
        f"{forecast['rain_mm']} mm\n\n"
        f"Rain Windows:\n"
        f"{rain_windows}"
    )


def format_day3_forecast(forecast):

    return (
        f"DAY 3 OUTLOOK\n\n"
        f"Summary: "
        f"{forecast['summary']}\n\n"
        f"Maximum Temperature: "
        f"{forecast['max_temp']}°C\n"
        f"Minimum Temperature: "
        f"{forecast['min_temp']}°C\n"
        f"Humidity: "
        f"{forecast['humidity']}%\n"
        f"Maximum Wind Speed: "
        f"{forecast['wind_speed']} km/h\n"
        f"Rain Probability: "
        f"{forecast['rain_probability']}%\n"
        f"Expected Rainfall: "
        f"{forecast['rain']} mm"
    )


def build_weather_report(
    location_name, current_weather, today_forecast, tomorrow_forecast, day3_forecast
):

    sections = [
        format_current_weather(current_weather),
        format_day_forecast("TODAY FORECAST", today_forecast),
        format_day_forecast("TOMORROW FORECAST", tomorrow_forecast),
        format_day3_forecast(day3_forecast),
    ]

    return "\n\n".join(sections)
