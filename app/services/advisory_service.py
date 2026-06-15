"""
Advisory engine.

Responsible for:
1. Loading advisory rules.
2. Loading weather schema.
3. Resolving advisory message placeholders.
"""

from pathlib import Path

import yaml

from app.services.imd_warning_service import get_imd_warning_fragments

CONFIG_DIR = Path(__file__).parent.parent / "config"


def load_advisory_rules() -> list[dict]:
    """
    Load advisory rules from YAML.

    Returns
    -------
    list[dict]
        Advisory rule definitions.
    """
    path = CONFIG_DIR / "advisory_rules.yaml"

    with open(path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    return config["rules"]


def get_nested_value(data: dict, path: str):
    """
    Fetch nested value using dot notation.

    Example
    -------
    path = "today.max_temp"

    Returns
    -------
    Any
    """
    value = data

    for part in path.split("."):
        value = value[part]

    return value


def resolve_placeholders(message: str, weather: dict) -> str:
    """
    Replace placeholders inside advisory messages.

    Example
    -------
    {today.max_temp_time}

    Parameters
    ----------
    message : str
        Advisory message template.

    weather : dict
        Weather payload.

    Returns
    -------
    str
        Rendered message.
    """
    start = message.find("{")

    while start != -1:
        end = message.find("}", start)

        if end == -1:
            break

        placeholder = message[start + 1 : end]

        value = get_nested_value(weather, placeholder)

        if isinstance(value, list):
            value = ", ".join(str(v) for v in value)

        message = message.replace(
            f"{{{placeholder}}}",
            str(value),
        )

        start = message.find("{")

    return message


def evaluate_condition(weather: dict, condition: dict) -> bool:
    """
    Evaluate a single condition.

    Parameters
    ----------
    weather : dict
    condition : dict

    Returns
    -------
    bool
    """
    metric = condition["metric"]

    operator = condition["operator"]

    expected = condition["value"]

    actual = get_nested_value(
        weather,
        metric,
    )

    if operator == ">":
        return actual > expected

    if operator == ">=":
        return actual >= expected

    if operator == "<":
        return actual < expected

    if operator == "<=":
        return actual <= expected

    if operator == "==":
        return actual == expected

    if operator == "!=":
        return actual != expected

    raise ValueError(f"Unsupported operator: {operator}")


def evaluate_rule(weather: dict, rule: dict) -> bool:
    """
    Evaluate a single rule.

    Parameters
    ----------
    weather : dict
    rule : dict

    Returns
    -------
    bool
    """
    if not rule["enabled"]:
        return False

    results = [
        evaluate_condition(
            weather,
            condition,
        )
        for condition in rule["conditions"]
    ]

    condition_type = rule["condition_type"]

    if condition_type == "all":
        return all(results)

    if condition_type == "any":
        return any(results)

    raise ValueError(f"Unsupported condition type: " f"{condition_type}")


def evaluate_rules(weather: dict) -> list[dict]:
    """
    Evaluate all advisory rules with priority and suppression support.

    Workflow:
    - Load advisory rules from YAML
    - Sort rules by descending priority
    - Evaluate each rule
    - Skip rules suppressed by previously fired rules
    - Resolve message placeholders
    - Return final advisory list

    Parameters
    ----------
    weather : dict
        Weather payload used for rule evaluation.

    Returns
    -------
    list[dict]
        Fired advisories containing:
        - id
        - category
        - priority
        - message
    """
    rules = load_advisory_rules()

    rules = sorted(
        rules,
        key=lambda rule: rule["priority"],
        reverse=True,
    )

    advisories = []

    suppressed_ids = set()

    for rule in rules:

        rule_id = rule["id"]

        if rule_id in suppressed_ids:
            continue

        if not evaluate_rule(
            weather,
            rule,
        ):
            continue

        advisories.append(
            {
                "id": rule["id"],
                "category": rule["category"],
                "priority": rule["priority"],
                "message": resolve_placeholders(
                    rule["message"],
                    weather,
                ),
            }
        )

        suppressed_ids.update(rule.get("suppresses", []))

    return advisories


def format_advisories(advisories: list[dict]) -> dict:
    """
    Format advisories into sections for WhatsApp template delivery.

    Rules are grouped by rule ID prefix:

    CUR  -> Current Conditions
    TD   -> Today's Advisory
    TM   -> Tomorrow's Advisory
    D3   -> Coming Days

    Parameters
    ----------
    advisories : list[dict]

    Returns
    -------
    dict
        Dictionary containing formatted advisory sections.
    """
    sections = {
        "current": [],
        "today": [],
        "tomorrow": [],
        "day3": [],
    }

    for advisory in advisories:

        rule_id = advisory["id"]

        message = advisory["message"].strip()

        if rule_id.startswith("CUR"):
            sections["current"].append(message)

        elif rule_id.startswith("TD"):
            sections["today"].append(message)

        elif rule_id.startswith("TM"):
            sections["tomorrow"].append(message)

        elif rule_id.startswith("D3"):
            sections["day3"].append(message)

    return {
        "current": " ".join(sections["current"]),
        "today": " ".join(sections["today"]),
        "tomorrow": " ".join(sections["tomorrow"]),
        "day3": " ".join(sections["day3"]),
    }


def build_rule_weather(payload: dict) -> dict:
    """
    Convert OpenWeather payload into
    rule-engine weather structure.

    Parameters
    ----------
    payload : dict

    Returns
    -------
    dict
    """
    current = payload["current_weather"]

    today = payload["today_forecast"]

    tomorrow = payload["tomorrow_forecast"]

    day3 = payload["day3_forecast"]

    return {
        "current": {
            "temp": current["temp"],
            "feels_like": current["feels_like"],
            "humidity": current["humidity"],
            "wind": current["wind_speed"],
            "rain": current["rain"],
        },
        "today": {
            "summary": today["summary"],
            "max_temp": today["max_temp"]["value"],
            "max_temp_time": today["max_temp"]["time"],
            "min_temp": today["min_temp"]["value"],
            "min_temp_time": today["min_temp"]["time"],
            "max_humidity": today["max_humidity"]["value"],
            "max_humidity_time": today["max_humidity"]["time"],
            "max_wind": today["max_wind"]["value"],
            "max_wind_time": today["max_wind"]["time"],
            "rain_probability": today["rain_probability"],
            "rainfall": today["rain_mm"],
            "rain_windows": today["rain_windows"],
        },
        "tomorrow": {
            "summary": tomorrow["summary"],
            "max_temp": tomorrow["max_temp"]["value"],
            "max_temp_time": tomorrow["max_temp"]["time"],
            "min_temp": tomorrow["min_temp"]["value"],
            "min_temp_time": tomorrow["min_temp"]["time"],
            "max_humidity": tomorrow["max_humidity"]["value"],
            "max_humidity_time": tomorrow["max_humidity"]["time"],
            "max_wind": tomorrow["max_wind"]["value"],
            "max_wind_time": tomorrow["max_wind"]["time"],
            "rain_probability": tomorrow["rain_probability"],
            "rainfall": tomorrow["rain_mm"],
            "rain_windows": tomorrow["rain_windows"],
        },
        "day3": {
            "summary": day3["summary"],
            "max_temp": day3["max_temp"],
            "min_temp": day3["min_temp"],
            "humidity": day3["humidity"],
            "max_wind": day3["wind_speed"],
            "rain_probability": day3["rain_probability"],
            "rainfall": day3["rain"],
        },
    }


def append_imd_warnings(advisories: dict, greenhouse_district: str | None) -> dict:
    """
    Append IMD warning fragments to advisory sections.

    Parameters
    ----------
    advisories : dict
    greenhouse_district : str | None

    Returns
    -------
    dict
    """
    if not greenhouse_district:
        return advisories

    fragments = get_imd_warning_fragments(greenhouse_district)

    for section in (
        "today",
        "tomorrow",
        "day3",
    ):
        fragment = fragments.get(section)

        if not fragment:
            continue

        existing = advisories.get(
            section,
            "",
        ).strip()

        if existing:
            advisories[section] = f"{existing} {fragment}"
        else:
            advisories[section] = fragment

    return advisories


def generate_advisories(payload: dict, greenhouse_district: str | None = None) -> dict:
    """
    Generate advisories from YAML rules.

    Parameters
    ----------
    weather : dict

    Returns
    -------
    list[str]
    """
    weather = build_rule_weather(payload)

    advisories = evaluate_rules(weather)

    formatted = format_advisories(advisories)

    return append_imd_warnings(formatted, greenhouse_district)
