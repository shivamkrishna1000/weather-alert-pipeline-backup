from typing import Any, Dict, List, Tuple


def split_records(records: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict]]:
    """
    Split records based on presence of geographic coordinates.

    Separates records into those with valid latitude/longitude and those
    missing location data for downstream processing (e.g., geocoding).

    Parameters
    ----------
    records : list[dict]
        Raw greenhouse records.

    Returns
    -------
    tuple[list[dict], list[dict]]
        - Records with valid coordinates
        - Records missing coordinates
    """
    with_loc = []
    without_loc = []

    for r in records:
        if r.get("Latitude") is not None and r.get("Longitude") is not None:
            with_loc.append(r)
        else:
            without_loc.append(r)

    return with_loc, without_loc


def filter_greenhouses(
    records: List[Dict[str, Any]], allowed_statuses: set, fields: Dict
) -> List[Dict[str, Any]]:
    """
    Filter greenhouse records based on status and valid coordinates.

    Retains only records that:
    - Have allowed operational status
    - Contain both latitude and longitude

    Parameters
    ----------
    records : list[dict]
        Greenhouse records.
    allowed_statuses : set
        Valid greenhouse statuses.
    fields : dict
        Mapping of field names.

    Returns
    -------
    list[dict]
        Filtered list of valid greenhouse records.
    """
    filtered = []

    for record in records:
        status = record.get(fields["status"])
        latitude = record.get(fields["latitude"])
        longitude = record.get(fields["longitude"])

        if status not in allowed_statuses:
            continue

        if latitude is None or longitude is None:
            continue

        filtered.append(record)

    return filtered


def extract_fields(records: List[Dict[str, Any]], fields: Dict) -> List[Dict[str, Any]]:
    """
    Transform raw greenhouse records into structured format.

    Extracts relevant fields and standardizes keys for downstream storage.

    Parameters
    ----------
    records : list[dict]
        Filtered greenhouse records.
    fields : dict
        Mapping of field names from Zoho schema.

    Returns
    -------
    list[dict]
        Structured records with keys:
        - greenhouse_name
        - farmer_name
        - phone
        - latitude
        - longitude
        - district
        - taluk
        - village
        - status
        - id
    """
    cleaned = []

    for record in records:
        cleaned.append(
            {
                "greenhouse_name": record.get(fields["name"]),
                "farmer_name": (record.get(fields["farmer"]) or {}).get("name"),
                "phone": get_phone(record, fields["phone_fields"]),
                "latitude": record.get(fields["latitude"]),
                "longitude": record.get(fields["longitude"]),
                "district": record.get(fields["district"]),
                "taluk": record.get(fields["taluk"]),
                "village": record.get(fields["village"]),
                "state": record.get(fields["state"]),
                "region": record.get(fields["region"]),
                "status": record.get(fields["status"]),
                "id": record.get(fields["id"]),
            }
        )

    return cleaned


def get_phone(record, phone_fields):
    """
    Extract the first valid phone number from prioritized fields.

    Cleans the value by removing whitespace.

    Parameters
    ----------
    record : dict
        Greenhouse record.
    phone_fields : list
        Ordered list of phone field names.

    Returns
    -------
    str or None
        First valid phone number found, else None.
    """
    for field in phone_fields:
        value = record.get(field)
        if value:
            value = value.strip().replace(" ", "")
            return value
    return None
