def group_advisories_by_farmer(records: list[dict]) -> dict:
    """
    Group advisory records by farmer and greenhouse.

    Parameters
    ----------
    records : list[dict]
        Flat advisory records fetched from DB.

    Returns
    -------
    dict
        Mapping of phone → grouped data:
        {
            phone: {
                "farmer_name": str,
                "greenhouses": {
                    greenhouse_name: [advisories]
                },
                "ids": [list of advisory_log ids]
            }
        }
    """

    grouped = {}

    for r in records:
        phone = r["phone"]

        if not phone:
            continue  # skip invalid

        if phone not in grouped:
            grouped[phone] = {
                "farmer_name": r["farmer_name"],
                "advisories": [],
                "ids": [],
            }

        grouped[phone]["advisories"].append(r["advisory"])
        grouped[phone]["ids"].append(r["id"])

    return grouped


def split_advisory_sections(greenhouse_name: str, advisories: list[dict]) -> dict:
    """
    Convert stored advisory JSON into WATI template sections.

    Parameters
    ----------
    greenhouse_name : str
    advisories : list[dict]

    Returns
    -------
    dict
    """
    advisory = advisories[-1]

    return {
        "greenhouse": advisory.get(
            "greenhouse",
            greenhouse_name,
        ),
        "current": advisory.get("current")
        or "No significant current weather concerns.",
        "today": advisory.get("today") or "No specific advisory for today.",
        "tomorrow": advisory.get("tomorrow") or "No specific advisory for tomorrow.",
        "day3": advisory.get("day3") or "No specific advisory for coming days.",
    }
