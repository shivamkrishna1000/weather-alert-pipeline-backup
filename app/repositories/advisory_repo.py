from datetime import date

from psycopg2.extras import Json


def advisory_already_sent(connection, greenhouse_id: str, advisory: dict) -> bool:
    """
    Check if an advisory has already been sent to a greenhouse today.

    Parameters
    ----------
    connection : Any
        Database connection.
    greenhouse_id : str
        Unique greenhouse identifier.
    advisory : str
        Advisory message.

    Returns
    -------
    bool
        True if advisory already exists for today, else False.
    """
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT 1 FROM advisory_logs
        WHERE greenhouse_id = %s
        AND advisory = %s
        AND advisory_date = %s
        LIMIT 1
        """,
        (greenhouse_id, Json(advisory), date.today()),
    )

    exists = cursor.fetchone() is not None
    cursor.close()
    return exists


def insert_advisory_log(
    connection, greenhouse: dict, cluster_key: str, advisory: str
) -> None:
    """
    Insert advisory delivery log for a greenhouse.

    Parameters
    ----------
    connection : Any
        Database connection.
    greenhouse : dict
        Greenhouse record containing id, farmer_name, phone.
    cluster_key : str
        Cluster identifier.
    advisory : str
        Advisory message.

    Returns
    -------
    None
    """
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO advisory_logs (
            greenhouse_id,
            greenhouse_name,
            farmer_name,
            phone,
            cluster_key,
            advisory,
            advisory_date,
            delivery_status
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (greenhouse_id, advisory, advisory_date)
        DO NOTHING
        """,
        (
            greenhouse["id"],
            greenhouse["name"],
            greenhouse["farmer_name"],
            greenhouse["phone"],
            cluster_key,
            Json(advisory),
            date.today(),
            "pending",
        ),
    )

    connection.commit()
    cursor.close()


def fetch_pending_advisories(connection) -> list[dict]:
    """
    Fetch all pending advisory logs for delivery.

    Retrieves advisory records that have not yet been sent.
    These records will be grouped and processed by the delivery pipeline.

    Parameters
    ----------
    connection : Any
        Database connection.

    Returns
    -------
    list[dict]
        List of advisory records with keys:
        - id
        - greenhouse_id
        - greenhouse_name
        - farmer_name
        - phone
        - advisory
    """
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            greenhouse_id,
            greenhouse_name,
            farmer_name,
            phone,
            advisory
        FROM advisory_logs
        WHERE delivery_status = 'pending'
        """
    )

    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    cursor.close()

    return [dict(zip(columns, row)) for row in rows]


def mark_advisories_as_sent(connection, ids: list[int]) -> None:
    """
    Mark advisory logs as sent.

    Parameters
    ----------
    connection : Any
        Database connection.
    ids : list[int]
        List of advisory_log IDs to update.

    Returns
    -------
    None
    """
    if not ids:
        return

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE advisory_logs
        SET delivery_status = 'sent',
            sent_at = NOW()
        WHERE id = ANY(%s)
        """,
        (ids,),
    )

    connection.commit()
    cursor.close()


def delete_pending_advisories(connection, greenhouse_id: str) -> None:
    """
    Remove pending advisory logs for a greenhouse.

    This is used before inserting a newly generated advisory
    so that only the most recent pending advisory remains
    available for delivery.

    Sent advisories are preserved for historical tracking.

    Parameters
    ----------
    connection : Any
        Database connection.
    greenhouse_id : str
        Unique greenhouse identifier.

    Returns
    -------
    None
    """
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM advisory_logs
        WHERE greenhouse_id = %s
        AND delivery_status = 'pending'
        """,
        (greenhouse_id,),
    )

    connection.commit()

    cursor.close()
