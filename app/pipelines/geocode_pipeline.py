from concurrent.futures import ThreadPoolExecutor, as_completed

from app.database import get_connection
from app.external.maps_client import geocode_address
from app.repositories.greenhouse_repo import (
    fetch_missing_batch,
    get_from_cache,
    increment_attempt,
    insert_into_cache,
)
from app.services.geocode_service import prepare_address, should_retry


def insert_geocoded_record(connection, record: dict, lat: float, lon: float) -> None:
    """
    Insert or update a greenhouse record with geocoded coordinates.

    Performs an upsert into the `greenhouses` table, updating latitude,
    longitude, and marking the record as geocoded.

    Parameters
    ----------
    connection : Any
        Active database connection.
    record : dict
        Greenhouse record containing at least 'id', 'name',
        'farmer_name', 'phone', and 'status'.
    lat : float
        Latitude value.
    lon : float
        Longitude value.

    Returns
    -------
    None
    """
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO greenhouses
        (id, name, farmer_name, phone, latitude, longitude, district, taluk, village, state, region, status, geocoded)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
        ON CONFLICT(id) DO UPDATE SET
            district = EXCLUDED.district,
            taluk = EXCLUDED.taluk,
            village = EXCLUDED.village,
            state = EXCLUDED.state,
            region = EXCLUDED.region,
            latitude=EXCLUDED.latitude,
            longitude=EXCLUDED.longitude,
            geocoded=True
        """,
        (
            record["id"],
            record["name"],
            record["farmer_name"],
            record["phone"],
            lat,
            lon,
            record.get("district"),
            record.get("taluk"),
            record.get("village"),
            record.get("state"),
            record.get("region"),
            record["status"],
        ),
    )

    connection.commit()
    cursor.close()


def delete_from_missing(connection, record_id: str) -> None:
    """
    Remove a record from the missing-location table after successful geocoding.

    Parameters
    ----------
    connection : Any
        Database connection.
    record_id : str
        Unique identifier of the greenhouse record.

    Returns
    -------
    None
    """
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM greenhouses_missing_location WHERE id = %s",
        (record_id,),
    )

    connection.commit()
    cursor.close()


def run_geocode_pipeline(connection, database_url: str, batch_size: int = 100) -> None:
    """
    Execute geocoding pipeline for records missing location data.

    The pipeline processes records in batches:
    - Fetch records with missing coordinates
    - Build address strings
    - Attempt geocoding (with retry limits)
    - Use cache when available
    - Persist successful results and remove processed records

    Processing is performed in parallel using a thread pool.

    Parameters
    ----------
    connection : Any
        Database connection.
    database_url : str
        Database URL used to create independent connections for parallel workers.
    batch_size : int, optional
        Number of records to process per batch.

    Returns
    -------
    None

    Raises
    ------
    RuntimeError
        If a critical failure occurs during parallel execution.
    """
    total_processed = 0

    while True:
        records = fetch_missing_batch(connection, batch_size)

        if not records:
            print("No more records to process.")
            break

        print(f"Processing batch of {len(records)} records...")

        MAX_WORKERS = 20

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [
                executor.submit(process_record_parallel, record, database_url)
                for record in records
            ]

            for future in as_completed(futures):
                try:
                    processed = future.result()

                    if processed:
                        total_processed += 1

                except RuntimeError as e:
                    print(f"Critical failure: {e}")
                    raise

    print(f"Total processed: {total_processed}")


def handle_failed_geocode(connection, record_id: str) -> None:
    """
    Increment retry attempt count for a failed geocoding record.

    Parameters
    ----------
    connection : Any
        Database connection.
    record_id : str
        Record identifier.

    Returns
    -------
    None
    """
    increment_attempt(connection, record_id)


def get_coordinates(
    connection, address: str, record_id: str
) -> tuple[float, float] | None:
    """
    Resolve geographic coordinates using cache or external API.

    Workflow:
    - Check local cache for existing coordinates
    - If not found, call geocoding API
    - Store successful results in cache

    Parameters
    ----------
    connection : Any
        Database connection.
    address : str
        Address string to geocode.
    record_id : str
        Record identifier (used for logging and retry tracking).

    Returns
    -------
    tuple[float, float] or None
        Latitude and longitude if successful.

    Raises
    ------
    ValueError
        If address is invalid.
    RuntimeError
        If API request fails.
    """
    cached = get_from_cache(connection, address)

    if cached:
        print(f"Cache hit: {address}")
        return cached

    try:
        print(f"Calling API: {address}")
        lat, lon = geocode_address(address)
        insert_into_cache(connection, address, lat, lon)
        return lat, lon

    except ValueError:
        print(f"Geocode failed (invalid address): {record_id}")
        handle_failed_geocode(connection, record_id)
        raise

    except RuntimeError as e:
        print(f"API error: {e}")
        raise


def process_record(connection, record: dict) -> bool:
    """
    Process a single record through the geocoding workflow.

    Steps:
    - Build address from record
    - Check retry eligibility
    - Resolve coordinates (cache or API)
    - Persist results and clean up

    Parameters
    ----------
    connection : Any
        Database connection.
    record : dict
        Greenhouse record.

    Returns
    -------
    bool
        True if successfully geocoded and stored, False otherwise.
    """
    try:
        record_id = record.get("id")
        print(f"Processing ID: {record_id}")

        address = prepare_address(record)
        if not address:
            return False

        if not should_retry(record.get("attempts", 0)):
            return False

        coords = get_coordinates(connection, address, record_id)
        if not coords:
            return False

        lat, lon = coords

        persist_geocoded_result(connection, record, lat, lon)

        return True

    except (ValueError, RuntimeError) as e:
        print(f"Error processing record {record.get('id')}: {e}")
        return False


def process_record_parallel(record: dict, database_url: str) -> bool:
    """
    Execute record processing in isolation using a separate DB connection.

    This function is designed for parallel execution and ensures each
    worker manages its own database connection lifecycle.

    Parameters
    ----------
    record : dict
        Greenhouse record.
    database_url : str
        Database URL used to create a new connection.

    Returns
    -------
    bool
        Result of record processing.
    """
    connection = get_connection(database_url)

    try:
        result = process_record(connection, record)
        return result

    finally:
        connection.close()


def persist_geocoded_result(connection, record: dict, lat: float, lon: float) -> None:
    """
    Store geocoded coordinates and remove record from pending queue.

    This performs two operations:
    - Upsert into `greenhouses` table
    - Delete from `greenhouses_missing_location`

    Parameters
    ----------
    connection : Any
        Database connection.
    record : dict
        Greenhouse record.
    lat : float
        Latitude value.
    lon : float
        Longitude value.

    Returns
    -------
    None
    """
    record_id = record["id"]

    insert_geocoded_record(connection, record, lat, lon)
    print(f"Inserted: {record_id}")

    delete_from_missing(connection, record_id)
    print(f"Deleted: {record_id}")
