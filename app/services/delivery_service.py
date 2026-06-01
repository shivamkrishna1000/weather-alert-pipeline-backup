from collections import defaultdict


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
                "greenhouses": defaultdict(list),
                "ids": [],
            }

        gh_name = r["greenhouse_name"] or "Unknown Greenhouse"

        grouped[phone]["greenhouses"][gh_name].append(r["advisory"])
        grouped[phone]["ids"].append(r["id"])

    return grouped


def format_greenhouse_message(greenhouse_name: str, advisories: list[str]) -> str:
    """
    Format message for a single greenhouse.

    Parameters
    ----------
    greenhouse_name : str
    advisories : list[str]

    Returns
    -------
    str
    """
    advisory_text = "\n\n".join(advisories)

    return f"*{greenhouse_name}*\n\n" f"{advisory_text}"
