"""
Database module for storing greenhouse data.
"""

from app.constants import ZOHO_FIELDS
from app.core.greenhouse import get_phone


def insert_greenhouses(connection, records: list[dict]) -> None:
    """
    Insert or update greenhouse records in the database.

    Parameters
    ----------
    connection : Any
        Database connection.
    records : List[Dict]
        List of greenhouse records.

    Returns
    -------
    None
    """
    cursor = connection.cursor()

    for r in records:
        cursor.execute(
            """
            INSERT INTO greenhouses (id, name, farmer_name, phone, latitude, longitude, district, taluk, village, status, geocoded)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT(id) DO UPDATE SET
                name = COALESCE(excluded.name, greenhouses.name),
                farmer_name = COALESCE(excluded.farmer_name, greenhouses.farmer_name),
                phone = COALESCE(excluded.phone, greenhouses.phone),
                latitude = COALESCE(excluded.latitude, greenhouses.latitude),
                longitude = COALESCE(excluded.longitude, greenhouses.longitude),
                district = COALESCE(excluded.district, greenhouses.district),
                taluk = COALESCE(excluded.taluk, greenhouses.taluk),
                village = COALESCE(excluded.village, greenhouses.village),
                status = COALESCE(excluded.status, greenhouses.status),
                geocoded = excluded.geocoded
            """,
            (
                r.get("id"),
                r.get("greenhouse_name"),
                r.get("farmer_name"),
                r.get("phone"),
                r.get("latitude"),
                r.get("longitude"),
                r.get("district"),
                r.get("taluk"),
                r.get("village"),
                r.get("status"),
                False,
            ),
        )

    connection.commit()
    cursor.close()


def insert_missing_location(connection, records: list[dict]) -> None:
    """
    Insert or update records missing location data.

    Parameters
    ----------
    connection : Any
        Database connection.
    records : List[Dict]
        List of greenhouse records.

    Returns
    -------
    None
    """
    cursor = connection.cursor()

    for r in records:
        cursor.execute(
            """
            INSERT INTO greenhouses_missing_location
            (id, name, farmer_name, phone, status, village, taluk, district, state, region, attempts)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                farmer_name=excluded.farmer_name,
                phone=excluded.phone,
                status=excluded.status,
                village=excluded.village,
                taluk=excluded.taluk,
                district=excluded.district,
                state=excluded.state,
                region=excluded.region
            """,
            (
                r.get(ZOHO_FIELDS["id"]),
                r.get(ZOHO_FIELDS["name"]),
                (r.get(ZOHO_FIELDS["farmer"]) or {}).get("name"),
                get_phone(r, ZOHO_FIELDS["phone_fields"]),
                r.get(ZOHO_FIELDS["status"]),
                r.get(ZOHO_FIELDS["village"]),
                r.get(ZOHO_FIELDS["taluk"]),
                r.get(ZOHO_FIELDS["district"]),
                r.get(ZOHO_FIELDS["state"]),
                r.get(ZOHO_FIELDS["region"]),
                0,
            ),
        )

    connection.commit()
    cursor.close()


def get_existing_ids(connection) -> set:
    """
    Fetch all existing greenhouse IDs from database.

    Parameters
    ----------
    connection : Any
        Database connection.

    Returns
    -------
    Set
        Set of greenhouse IDs.
    """
    cursor = connection.cursor()

    cursor.execute("SELECT id FROM greenhouses")
    rows = cursor.fetchall()

    cursor.close()

    return {row[0] for row in rows}


def get_last_sync_time(connection) -> str | None:
    """
    Retrieve last synchronization timestamp.

    Parameters
    ----------
    connection : Any
        Database connection.

    Returns
    -------
    Optional[str]
        Last sync timestamp if exists.
    """
    cursor = connection.cursor()

    cursor.execute("SELECT value FROM sync_metadata WHERE key='last_sync'")
    row = cursor.fetchone()

    cursor.close()

    return row[0] if row else None


def get_from_cache(connection, address: str) -> tuple[float, float] | None:
    """
    Fetch cached geocode result for an address.

    Parameters
    ----------
    connection : Any
        Database connection.
    address : str
        Address string.

    Returns
    -------
    Optional[Tuple[float, float]]
        Cached latitude and longitude if exists.
    """
    cursor = connection.cursor()

    cursor.execute(
        "SELECT latitude, longitude FROM geocode_cache WHERE address = %s",
        (address,),
    )

    row = cursor.fetchone()
    cursor.close()

    if row:
        return row  # (lat, lon)

    return None


def insert_into_cache(
    connection, address: str, latitude: float, longitude: float
) -> None:
    """
    Store geocode result in cache.

    Parameters
    ----------
    connection : Any
        Database connection.
    address : str
        Address string.
    latitude : float
        Latitude value.
    longitude : float
        Longitude value.

    Returns
    -------
    None
    """
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO geocode_cache (address, latitude, longitude)
        VALUES (%s, %s, %s)
        ON CONFLICT (address) DO UPDATE SET
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude
        """,
        (address, latitude, longitude),
    )

    connection.commit()
    cursor.close()


def fetch_missing_batch(connection, limit: int = 100) -> list[dict]:
    """
    Fetch batch of records missing location data.

    Parameters
    ----------
    connection : Any
        Database connection.
    limit : int, optional
        Number of records to fetch.

    Returns
    -------
    List[Dict]
        List of records.
    """
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT * FROM greenhouses_missing_location
        WHERE attempts < 3
        LIMIT %s
        """,
        (limit,),
    )

    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    cursor.close()

    records = [dict(zip(columns, row)) for row in rows]

    return records


def increment_attempt(connection, record_id: str) -> None:
    """
    Increment retry attempt count for a record.

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
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE greenhouses_missing_location
        SET attempts = attempts + 1
        WHERE id = %s
        """,
        (record_id,),
    )

    connection.commit()
    cursor.close()


def delete_greenhouse(connection, greenhouse_id: str) -> None:
    """
    Delete greenhouse record from both main and missing tables.

    Parameters
    ----------
    greenhouse_id : str
        Unique greenhouse identifier.
    """
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM greenhouses WHERE id = %s",
        (greenhouse_id,),
    )

    cursor.execute(
        "DELETE FROM greenhouses_missing_location WHERE id = %s",
        (greenhouse_id,),
    )

    connection.commit()
    cursor.close()


def update_cluster_key(connection, greenhouse_id: str, cluster_key: str) -> None:
    """
    Update cluster_key for a greenhouse.

    Parameters
    ----------
    connection : Any
        Database connection.
    greenhouse_id : str
        Greenhouse ID.
    cluster_key : str
        Assigned cluster key.
    """
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE greenhouses
        SET cluster_key = %s
        WHERE id = %s
        """,
        (cluster_key, greenhouse_id),
    )
    connection.commit()
    cursor.close()
