def insert_weather_snapshots(
    connection,
    latitude: float,
    longitude: float,
    comparison_data: dict,
):
    """
    Persist both provider snapshots.
    """

    cursor = connection.cursor()

    providers = [
        "weatherapi",
        "openweather",
    ]

    for provider in providers:

        current = comparison_data[provider]["current"]

        forecast = comparison_data[provider]["forecast"]

        rain_window = forecast.get("rain_window") or {}

        cursor.execute(
            """
            INSERT INTO rnd_weather_provider_snapshots (

                provider,

                latitude,
                longitude,

                current_temp,
                current_feels_like,
                current_humidity,
                current_wind,
                current_rain,
                current_rain_probability,

                max_temp,
                max_temp_time,

                min_temp,
                min_temp_time,

                max_humidity,
                max_humidity_time,

                max_wind,
                max_wind_time,

                max_rain_probability,
                max_rain_probability_time,

                rain_window_start,
                rain_window_end

            )

            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                provider,
                latitude,
                longitude,
                current["temp"],
                current["feels_like"],
                current["humidity"],
                current["wind"],
                current["rain"],
                current["rain_probability"],
                forecast["max_temp"]["value"],
                forecast["max_temp"]["time"],
                forecast["min_temp"]["value"],
                forecast["min_temp"]["time"],
                forecast["max_humidity"]["value"],
                forecast["max_humidity"]["time"],
                forecast["max_wind"]["value"],
                forecast["max_wind"]["time"],
                forecast["max_rain_probability"]["value"],
                forecast["max_rain_probability"]["time"],
                rain_window.get("start"),
                rain_window.get("end"),
            ),
        )

    connection.commit()

    cursor.close()
