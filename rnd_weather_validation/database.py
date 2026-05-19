from psycopg2.extras import Json


def create_rnd_tables(connection) -> None:
    """
    Create R&D validation tables.
    """

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS
        rnd_weather_snapshots (

            id SERIAL PRIMARY KEY,

            location_name TEXT
            NOT NULL,

            collected_at TIMESTAMP
            DEFAULT NOW(),

            current_weather JSONB
            NOT NULL,

            today_forecast JSONB
            NOT NULL,

            tomorrow_forecast JSONB
            NOT NULL,

            day3_forecast JSONB
            NOT NULL,

            weather_report TEXT
            NOT NULL
        )
        """
    )

    connection.commit()
    cursor.close()


def insert_weather_snapshot(
    connection,
    location_name,
    current_weather,
    today_forecast,
    tomorrow_forecast,
    day3_forecast,
    weather_report,
) -> None:

    cursor = connection.cursor()

    query = """
        INSERT INTO rnd_weather_snapshots (location_name, current_weather, today_forecast, tomorrow_forecast, day3_forecast, weather_report)
        VALUES (%s, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb, %s)
    """

    values = (
        location_name,
        Json(current_weather),
        Json(today_forecast),
        Json(tomorrow_forecast),
        Json(day3_forecast),
        weather_report,
    )

    cursor.execute(query, values)
    connection.commit()
    cursor.close()
