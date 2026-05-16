"""
Entry point for greenhouse data pipeline.
"""

import sys

import psycopg2

from app.config import get_database_url, load_environment
from app.database import get_connection
from app.pipelines.delivery_pipeline import run_delivery_pipeline
from app.pipelines.geocode_pipeline import run_geocode_pipeline
from app.pipelines.sync_pipeline import run_sync_pipeline
from app.pipelines.weather_pipeline import run_weather_pipeline


def run_weekly_pipeline(connection, database_url: str) -> None:
    """
    Execute the weekly data pipeline.

    This pipeline handles operations that are expensive and do not need
    to run frequently:
    1. Synchronize greenhouse data from Zoho
    2. Geocode records missing latitude/longitude

    Parameters
    ----------
    connection : Any
        Active database connection.
    database_url : str
        Database connection string used for creating new connections
        inside geocoding workers.

    Returns
    -------
    None

    Notes
    -----
    - Intended to be run on a weekly schedule.
    - Ensures the greenhouse dataset is up-to-date and fully geocoded
      before weather processing.
    """
    print("Starting weekly pipeline...")

    print("Starting greenhouse sync...")
    run_sync_pipeline(connection)
    print("Greenhouse sync completed.")

    print("Starting geocoding pipeline...")
    run_geocode_pipeline(connection, database_url, batch_size=100)
    print("Geocoding completed.")

    print("Weekly pipeline completed.")


def run_daily_pipeline(connection) -> None:
    """
    Execute the daily advisory pipeline.

    This pipeline handles operations that depend on frequently changing data:
    1. Fetch and process weather data for clusters
    2. Generate advisories
    3. Deliver messages to farmers

    Parameters
    ----------
    connection : Any
        Active database connection.

    Returns
    -------
    None

    Notes
    -----
    - Intended to be run daily (or multiple times per day if needed).
    - Weather fetching respects cache freshness to avoid redundant API calls.
    - Delivery only processes advisories with 'pending' status.
    """
    print("Starting daily pipeline...")

    print("Starting weather pipeline...")
    run_weather_pipeline(connection)
    print("Weather pipeline completed.")

    print("Starting delivery pipeline...")

    # Retry delivery once if DB connection becomes stale
    try:
        run_delivery_pipeline(connection)

    except psycopg2.OperationalError as e:
        print(f"Database connection lost before delivery: {e}")
        print("Reconnecting and retrying delivery pipeline...")

        connection.close()

        database_url = get_database_url()
        new_connection = get_connection(database_url)

        try:
            run_delivery_pipeline(new_connection)
        finally:
            new_connection.close()

    print("Delivery pipeline completed.")

    print("Daily pipeline completed.")


def main() -> None:
    """
    Entry point for pipeline execution.

    This function routes execution based on the provided command-line argument.

    Supported modes:
    - 'weekly' : Runs sync and geocoding pipelines
    - 'daily'  : Runs weather processing and delivery pipelines

    Usage
    -----
    python -m app.main weekly
    python -m app.main daily

    Returns
    -------
    None

    Raises
    ------
    ValueError
        If no mode is provided or an invalid mode is specified.
    RuntimeError
        If any pipeline stage fails critically.

    Notes
    -----
    - Environment variables must be loaded before execution.
    - A single database connection is created and shared where appropriate.
    - Connection is safely closed after execution.
    """
    load_environment()

    if len(sys.argv) < 2:
        print("Usage: python -m app.main [weekly|daily]")
        return

    mode = sys.argv[1].lower()

    connection = None

    try:
        database_url = get_database_url()
        connection = get_connection(database_url)

        print("Database connected.")

        if mode == "weekly":
            run_weekly_pipeline(connection, database_url)

        elif mode == "daily":
            run_daily_pipeline(connection)

        else:
            print("Invalid mode. Use 'weekly' or 'daily'.")
            return

    except (RuntimeError, ValueError) as e:
        print(f"Error occurred: {e}")
        raise

    finally:
        if connection:
            connection.close()
            print("Database connection closed.")


if __name__ == "__main__":
    main()
