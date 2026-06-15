"""
IMD warning service.

Handles:
- District mapping lookup
- IMD district resolution
"""

import csv
import time
from pathlib import Path

from app.constants import (
    IMD_ALERT_EMOJIS,
    IMD_COLOR_MAPPING,
    IMD_ENABLED_ALERT_LEVELS,
    IMD_WARNING_CODE_DESCRIPTIONS,
)
from app.external.imd_client import fetch_district_warnings

_MAPPING_CACHE = None
_IMD_RECORD_CACHE = None
_IMD_CACHE_TIME = 0

# 30 minutes
IMD_CACHE_TTL_SECONDS = 1800


def load_district_mapping() -> dict[str, str]:
    """
    Load greenhouse district to IMD Obj_id mapping.

    Returns
    -------
    dict[str, str]
        Mapping:

        {
            greenhouse_district: imd_obj_id
        }

    Notes
    -----
    - Mapping file is loaded once.
    - Result is cached in memory.
    """
    global _MAPPING_CACHE

    if _MAPPING_CACHE is not None:
        return _MAPPING_CACHE

    csv_path = Path(__file__).parent.parent / "district_mapping.csv"

    mapping = {}

    with open(
        csv_path,
        "r",
        encoding="utf-8-sig",
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:

            greenhouse_district = row["greenhouse_district"].strip().upper()

            imd_obj_id = row["imd_obj_id"].strip()

            mapping[greenhouse_district] = imd_obj_id

    _MAPPING_CACHE = mapping

    return mapping


def get_imd_obj_id(greenhouse_district: str) -> str | None:
    """
    Resolve IMD Obj_id from greenhouse district.

    Parameters
    ----------
    greenhouse_district : str

    Returns
    -------
    str | None
        IMD Obj_id if found.
    """
    if not greenhouse_district:
        return None

    mapping = load_district_mapping()

    return mapping.get(greenhouse_district.strip().upper())


def load_imd_records() -> dict[str, dict]:
    """
    Load IMD warning records indexed by Obj_id.

    Returns
    -------
    dict[str, dict]
        Mapping:

        {
            obj_id: record
        }

    Notes
    -----
    IMD warning data is cached for a limited
    period to avoid repeated API calls during
    a single pipeline execution.
    """
    global _IMD_RECORD_CACHE
    global _IMD_CACHE_TIME

    current_time = time.time()

    if (
        _IMD_RECORD_CACHE is not None
        and current_time - _IMD_CACHE_TIME < IMD_CACHE_TTL_SECONDS
    ):
        return _IMD_RECORD_CACHE

    print("Fetching fresh IMD dataset...")
    records = fetch_district_warnings()

    indexed = {}

    for record in records:

        obj_id = str(record.get("Obj_id", "")).strip()

        if not obj_id:
            continue

        indexed[obj_id] = record

    _IMD_RECORD_CACHE = indexed
    _IMD_CACHE_TIME = current_time

    return indexed


def get_imd_record(greenhouse_district: str) -> dict | None:
    """
    Resolve IMD warning record for a greenhouse district.

    Parameters
    ----------
    greenhouse_district : str

    Returns
    -------
    dict | None
        Matching IMD record if found.
    """
    obj_id = get_imd_obj_id(greenhouse_district)

    if not obj_id:
        return None

    records = load_imd_records()

    return records.get(str(obj_id))


def parse_warning_codes(warning_string: str) -> list[str]:
    """
    Convert IMD warning codes into readable text.

    Parameters
    ----------
    warning_string : str

    Returns
    -------
    list[str]
        Warning descriptions.
    """
    if not warning_string:
        return []

    warnings = []

    for code in warning_string.split(","):

        code = code.strip()

        if not code:
            continue

        try:
            warning_code = int(code)

        except ValueError:
            continue

        description = IMD_WARNING_CODE_DESCRIPTIONS.get(warning_code)

        if description:
            warnings.append(description)

    return warnings


def get_alert_color(color_code: str) -> str | None:
    """
    Resolve IMD color from color code.

    Parameters
    ----------
    color_code : str

    Returns
    -------
    str | None
    """
    try:
        color_code = int(color_code)

    except (TypeError, ValueError):
        return None

    return IMD_COLOR_MAPPING.get(color_code)


def build_warning_fragment(color: str, warnings: list[str]) -> str | None:
    """
    Build advisory text fragment.

    Parameters
    ----------
    color : str
    warnings : list[str]

    Returns
    -------
    str | None
    """
    if color not in IMD_ENABLED_ALERT_LEVELS:
        return None

    if not warnings:
        return None

    emoji = IMD_ALERT_EMOJIS.get(color, "")

    warning_text = ", ".join(warnings)

    return f"{emoji} IMD {color} Alert: " f"{warning_text} expected in your district."


def get_day_fragment(record: dict, day_key: str, color_key: str) -> str | None:
    """
    Build IMD advisory fragment for a single day.

    Parameters
    ----------
    record : dict
        IMD district warning record.
    day_key : str
        Day warning field name.
    color_key : str
        Day color field name.

    Returns
    -------
    str | None
        Advisory fragment if alert is enabled,
        otherwise None.
    """
    warnings = parse_warning_codes(record.get(day_key, ""))

    color = get_alert_color(record.get(color_key))

    return build_warning_fragment(
        color=color,
        warnings=warnings,
    )


def get_imd_warning_fragments(greenhouse_district: str) -> dict[str, str | None]:
    """
    Resolve IMD warning fragments for a greenhouse district.

    Parameters
    ----------
    greenhouse_district : str

    Returns
    -------
    dict[str, str | None]
        Example:

        {
            "today": "...",
            "tomorrow": "...",
            "day3": "..."
        }
    """
    record = get_imd_record(greenhouse_district)

    if not record:
        return {
            "today": None,
            "tomorrow": None,
            "day3": None,
        }

    return {
        "today": get_day_fragment(
            record,
            "Day_1",
            "Day1_Color",
        ),
        "tomorrow": get_day_fragment(
            record,
            "Day_2",
            "Day2_Color",
        ),
        "day3": get_day_fragment(
            record,
            "Day_3",
            "Day3_Color",
        ),
    }
