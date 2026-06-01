"""
Database module for storing greenhouse data.
"""

import psycopg2


def get_connection(database_url: str):
    """
    Create a PostgreSQL database connection.

    Parameters
    ----------
    database_url : str
        Connection string for the PostgreSQL database.

    Returns
    -------
    connection
        Active database connection object.
    """
    return psycopg2.connect(database_url)


def create_tables(connection) -> None:
    """
    Create required database tables if they do not exist.

    Tables created:
    - greenhouses
    - greenhouses_missing_location
    - sync_metadata
    - geocode_cache
    - weather_cache
    - weather_data

    Parameters
    ----------
    connection : Any
        Database connection.

    Returns
    -------
    None
    """
    cursor = connection.cursor()

    # Table with location
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS greenhouses (
            id TEXT PRIMARY KEY,
            name TEXT,
            farmer_name TEXT,
            phone TEXT,
            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION,
            district TEXT,
            taluk TEXT,
            village TEXT,
            status TEXT,
            geocoded BOOLEAN DEFAULT FALSE
        )
        """
    )

    # Table without location
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS greenhouses_missing_location (
            id TEXT PRIMARY KEY,
            name TEXT,
            farmer_name TEXT,
            phone TEXT,
            status TEXT,
            village TEXT,
            taluk TEXT,
            district TEXT,
            state TEXT,
            region TEXT,
            attempts INTEGER DEFAULT 0
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sync_metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS geocode_cache (
            address TEXT PRIMARY KEY,
            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS weather_cache (
            cluster_key TEXT PRIMARY KEY,

            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION,

            current_weather JSONB,
            today_forecast JSONB,
            tomorrow_forecast JSONB,
            day3_forecast JSONB,

            fetched_at TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS weather_data (
            id SERIAL PRIMARY KEY,

            cluster_key TEXT,

            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION,

            current_weather JSONB,
            today_forecast JSONB,
            tomorrow_forecast JSONB,
            day3_forecast JSONB,

            fetched_at TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS advisory_logs (
            id SERIAL PRIMARY KEY,

            greenhouse_id TEXT,
            greenhouse_name TEXT,

            farmer_name TEXT,
            phone TEXT,

            cluster_key TEXT,
            advisory TEXT,

            advisory_date DATE,

            delivery_status TEXT,
            sent_at TIMESTAMP DEFAULT NOW(),

            CONSTRAINT unique_advisory_per_day
            UNIQUE (greenhouse_id, advisory, advisory_date)
        )
        """
    )

    connection.commit()
    cursor.close()


def update_last_sync_time(connection, timestamp: str) -> None:
    """
    Insert or update the last synchronization timestamp.

    Performs an upsert into the `sync_metadata` table.

    Parameters
    ----------
    connection : Any
        Database connection.
    timestamp : str
        ISO formatted timestamp.

    Returns
    -------
    None
    """
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO sync_metadata (key, value)
        VALUES ('last_sync', %s)
        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
        """,
        (timestamp,),
    )

    connection.commit()
    cursor.close()
