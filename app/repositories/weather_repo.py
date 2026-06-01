"""
Database module for storing weather data.
"""

from datetime import UTC, datetime

from psycopg2.extras import Json

from app.config import get_cluster_mode
from app.services.cluster_service import build_cluster_key, build_distance_clusters


# -------- CLUSTER FUNCTIONS --------
def fetch_clusters(connection):
    """
    Fetch and build clusters with cluster_key assignment.

    Parameters
    ----------
    connection : Any

    Returns
    -------
    list[dict]
        Cluster summaries (without members)
    """
    records = fetch_greenhouse_records(connection)

    if not records:
        print("No greenhouse records found for clustering.")
        return []

    mode = get_cluster_mode()

    # Distance mode
    if mode == "distance":
        clusters = build_distance_clusters(records)

        return [
            {
                "cluster_key": c["cluster_key"],
                "latitude": c["latitude"],
                "longitude": c["longitude"],
                "members": c["members"],
            }
            for c in clusters
        ]

    # Taluk / Village mode
    clusters = aggregate_clusters(records)

    return [
        {
            "cluster_key": c["cluster_key"],
            "latitude": c["latitude"],
            "longitude": c["longitude"],
            "members": c["members"],
        }
        for c in clusters
    ]


def fetch_greenhouse_records(connection) -> list[dict]:
    """
    Fetch greenhouse records with valid coordinates.

    Parameters
    ----------
    connection : Any

    Returns
    -------
    list[dict]
        Greenhouse records with id, district, taluk, village, latitude, longitude
    """
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, name, farmer_name, phone, district, taluk, village, latitude, longitude
        FROM greenhouses
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        """
    )

    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]
    cursor.close()

    return [dict(zip(columns, row)) for row in rows]


def aggregate_clusters(records: list[dict]) -> list[dict]:
    """
    Aggregate greenhouse records into clusters (taluk/village mode).

    Parameters
    ----------
    records : list[dict]

    Returns
    -------
    list[dict]
        Clusters with members
    """
    clusters = {}

    for r in records:
        key = build_cluster_key(r)

        if not key:
            continue

        if key not in clusters:
            clusters[key] = {
                "latitude": [],
                "longitude": [],
                "members": [],
            }

        clusters[key]["latitude"].append(r["latitude"])
        clusters[key]["longitude"].append(r["longitude"])
        clusters[key]["members"].append(r)

    result = []

    for key, values in clusters.items():
        lat = sum(values["latitude"]) / len(values["latitude"])
        lon = sum(values["longitude"]) / len(values["longitude"])

        result.append(
            {
                "cluster_key": key,
                "latitude": lat,
                "longitude": lon,
                "members": values["members"],
            }
        )

    return result


# -------- CACHE FUNCTIONS --------
def get_cached_weather(connection, cluster_key: str) -> dict | None:
    """
    Retrieve cached weather payload.

    Parameters
    ----------
    connection : Any
    cluster_key : str

    Returns
    -------
    dict or None
    """
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT current_weather, today_forecast, tomorrow_forecast, day3_forecast, fetched_at FROM weather_cache WHERE cluster_key = %s
        """,
        (cluster_key,),
    )

    row = cursor.fetchone()

    cursor.close()

    if not row:
        return None
    (
        current_weather,
        today_forecast,
        tomorrow_forecast,
        day3_forecast,
        fetched_at,
    ) = row

    return {
        "current_weather": current_weather,
        "today_forecast": today_forecast,
        "tomorrow_forecast": tomorrow_forecast,
        "day3_forecast": day3_forecast,
        "fetched_at": fetched_at,
    }


def is_cache_fresh(fetched_at) -> bool:
    """
    Check if cached weather data is still valid.

    Parameters
    ----------
    fetched_at : datetime
        Timestamp of last fetch.
    ttl_hours : int
        Cache validity duration.

    Returns
    -------
    bool
    """
    if not fetched_at:
        return False

    # Ensure timezone-aware
    if fetched_at.tzinfo is None:
        fetched_at = fetched_at.replace(tzinfo=UTC)

    now = datetime.now(UTC)

    return fetched_at.date() == now.date()


# -------- WRITE FUNCTIONS --------
def upsert_weather_cache(connection, cluster: dict) -> None:
    """
    Store weather cache payload.

    Parameters
    ----------
    connection : Any
    cluster : dict

    Returns
    -------
    None
    """
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO weather_cache (
            cluster_key,
            latitude,
            longitude,

            current_weather,
            today_forecast,
            tomorrow_forecast,
            day3_forecast,

            fetched_at
        )
        VALUES (
            %s, %s, %s,
            %s::jsonb,
            %s::jsonb,
            %s::jsonb,
            %s::jsonb,
            NOW()
        )
        ON CONFLICT (cluster_key)
        DO UPDATE SET

            current_weather = EXCLUDED.current_weather,
            today_forecast = EXCLUDED.today_forecast,
            tomorrow_forecast = EXCLUDED.tomorrow_forecast,
            day3_forecast = EXCLUDED.day3_forecast,

            fetched_at = NOW()
        """,
        (
            cluster["cluster_key"],
            cluster["latitude"],
            cluster["longitude"],
            Json(cluster["current_weather"]),
            Json(cluster["today_forecast"]),
            Json(cluster["tomorrow_forecast"]),
            Json(cluster["day3_forecast"]),
        ),
    )

    connection.commit()

    cursor.close()


def insert_weather_history(connection, cluster: dict) -> None:
    """
    Insert historical weather payload.

    Parameters
    ----------
    connection : Any
    cluster : dict

    Returns
    -------
    None
    """
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO weather_data (
            cluster_key,

            latitude,
            longitude,

            current_weather,
            today_forecast,
            tomorrow_forecast,
            day3_forecast,

            fetched_at
        )
        VALUES (
            %s,
            %s,
            %s,

            %s::jsonb,
            %s::jsonb,
            %s::jsonb,
            %s::jsonb,

            NOW()
        )
        """,
        (
            cluster["cluster_key"],
            cluster["latitude"],
            cluster["longitude"],
            Json(cluster["current_weather"]),
            Json(cluster["today_forecast"]),
            Json(cluster["tomorrow_forecast"]),
            Json(cluster["day3_forecast"]),
        ),
    )

    connection.commit()

    cursor.close()
