def create_rnd_tables(connection) -> None:
    """
    Create R&D validation tables.
    """

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS rnd_weather_provider_snapshots (

            id SERIAL PRIMARY KEY,

            provider TEXT,

            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION,

            current_temp FLOAT,
            current_feels_like FLOAT,
            current_humidity FLOAT,
            current_wind FLOAT,
            current_rain FLOAT,
            current_rain_probability FLOAT,

            max_temp FLOAT,
            max_temp_time TEXT,

            min_temp FLOAT,
            min_temp_time TEXT,

            max_humidity FLOAT,
            max_humidity_time TEXT,

            max_wind FLOAT,
            max_wind_time TEXT,

            max_rain_probability FLOAT,
            max_rain_probability_time TEXT,

            rain_window_start TEXT,
            rain_window_end TEXT,

            fetched_at TIMESTAMP DEFAULT NOW()
        )
        """
    )

    connection.commit()

    cursor.close()
