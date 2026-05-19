import requests


def send_template_message(
    base_url: str, api_key: str, template_name: str, phone_number: str, parameters: list
):
    """
    Send WhatsApp template message via WATI.
    """

    url = f"{base_url}" f"/api/v1/sendTemplateMessage" f"?whatsappNumber={phone_number}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "template_name": template_name,
        "broadcast_name": "rnd_weather_validation",
        "parameters": [
            {
                "name": str(index),
                "value": str(value),
            }
            for index, value in enumerate(
                parameters,
                start=1,
            )
        ],
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
    )

    response.raise_for_status()
    return response.json()


def build_template_parameters(
    location_name,
    current_weather,
    today_forecast,
    tomorrow_forecast,
    day3_forecast,
):

    date = current_weather["datetime"].strftime("%d %B %Y")
    time = current_weather["datetime"].strftime("%I:%M %p")

    today_rain_windows = "\n".join(today_forecast["rain_windows"])

    tomorrow_rain_windows = "\n".join(tomorrow_forecast["rain_windows"])

    return [
        location_name,
        date,
        time,
        current_weather["temp"],
        current_weather["feels_like"],
        current_weather["humidity"],
        current_weather["wind_speed"],
        current_weather["rain"],
        today_forecast["summary"],
        today_forecast["max_temp"]["value"],
        today_forecast["max_temp"]["time"],
        today_forecast["min_temp"]["value"],
        today_forecast["min_temp"]["time"],
        today_forecast["max_humidity"]["value"],
        today_forecast["max_humidity"]["time"],
        today_forecast["max_wind"]["value"],
        today_forecast["max_wind"]["time"],
        today_forecast["rain_probability"],
        today_forecast["rain_mm"],
        today_rain_windows,
        tomorrow_forecast["summary"],
        tomorrow_forecast["max_temp"]["value"],
        tomorrow_forecast["max_temp"]["time"],
        tomorrow_forecast["min_temp"]["value"],
        tomorrow_forecast["min_temp"]["time"],
        tomorrow_forecast["max_humidity"]["value"],
        tomorrow_forecast["max_humidity"]["time"],
        tomorrow_forecast["max_wind"]["value"],
        tomorrow_forecast["max_wind"]["time"],
        tomorrow_forecast["rain_probability"],
        tomorrow_forecast["rain_mm"],
        tomorrow_rain_windows,
        day3_forecast["summary"],
        day3_forecast["max_temp"],
        day3_forecast["min_temp"],
        day3_forecast["humidity"],
        day3_forecast["wind_speed"],
        day3_forecast["rain_probability"],
        day3_forecast["rain"],
    ]
