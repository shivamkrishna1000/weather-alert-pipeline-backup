"""
Configuration and environment variable access module.

Provides helper functions to retrieve required configuration
values for external services and application settings.
"""

import os

from dotenv import load_dotenv


def load_environment() -> None:
    """Load environment variables from .env file."""
    load_dotenv()


def get_zoho_client_id() -> str:
    """Return Zoho client id."""
    val = os.environ.get("ZOHO_CLIENT_ID")
    if not val:
        raise ValueError("ZOHO_CLIENT_ID is not set")
    return val


def get_zoho_client_secret() -> str:
    """Return Zoho client secret."""
    val = os.environ.get("ZOHO_CLIENT_SECRET")
    if not val:
        raise ValueError("ZOHO_CLIENT_SECRET is not set")
    return val


def get_zoho_refresh_token() -> str:
    """Return Zoho refresh token."""
    val = os.environ.get("ZOHO_REFRESH_TOKEN")
    if not val:
        raise ValueError("ZOHO_REFRESH_TOKEN is not set")
    return val


def get_zoho_accounts_url() -> str:
    """Return Zoho account URL."""
    return os.environ.get("ZOHO_ACCOUNTS_URL", "https://accounts.zoho.com")


def get_zoho_api_base() -> str:
    """Return Zoho API base URL."""
    return os.environ.get("ZOHO_API_BASE", "https://www.zohoapis.com")


def get_zoho_module() -> str:
    """Return Zoho module name."""
    return os.environ.get("ZOHO_MODULE", "Greenhouse")


def get_google_maps_api_key() -> str:
    """Return Google Maps API key."""
    key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not key:
        raise ValueError("GOOGLE_MAPS_API_KEY is not set")
    return key


def get_database_url() -> str:
    """Return database URL."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL is not set")
    return db_url


def get_test_database_url() -> str:
    """Return test database URL."""
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        raise ValueError("TEST_DATABASE_URL is not set")
    return url


def get_openweather_api_key() -> str:
    """Return OpenWeather API key."""
    key = os.environ.get("OPENWEATHER_API_KEY")
    if not key:
        raise ValueError("OPENWEATHER_API_KEY is not set")
    return key


def get_cluster_mode() -> str:
    """Return Cluster Mode"""
    val = os.environ.get("CLUSTER_MODE", "taluk").lower()
    if val not in {"taluk", "village", "distance"}:
        raise ValueError("Invalid CLUSTER_MODE")
    return val


def is_pilot_mode() -> bool:
    """Return pilot mode flag."""
    val = os.environ.get("PILOT_MODE", "false").lower()
    return val == "true"


def get_pilot_villages() -> set[str]:
    """Return configured pilot villages."""
    raw = os.environ.get("PILOT_VILLAGES", "")
    if not raw.strip():
        return set()
    return {item.strip().upper() for item in raw.split(",") if item.strip()}


def get_wati_base_url() -> str:
    """Return WATI base URL."""
    val = os.environ.get("WATI_BASE_URL")
    if not val:
        raise ValueError("WATI_BASE_URL is not set")
    return val


def get_wati_api_token() -> str:
    """Return WATI API token."""
    val = os.environ.get("WATI_API_TOKEN")
    if not val:
        raise ValueError("WATI_API_TOKEN is not set")
    return val


def get_wati_template_name() -> str:
    """Return WATI template name."""
    val = os.environ.get("WATI_TEMPLATE_NAME")
    if not val:
        raise ValueError("WATI_TEMPLATE_NAME is not set")
    return val


def is_debug_mode() -> bool:
    """Return debug mode flag."""
    val = os.environ.get("DEBUG_MODE", "false").lower()
    return val == "true"


def get_imd_api_key() -> str:
    """Return IMD API key."""
    value = os.environ.get("IMD_API_KEY")

    if not value:
        raise ValueError("IMD_API_KEY is not set")

    return value


def get_imd_email() -> str:
    """Return IMD account email."""
    value = os.environ.get("IMD_EMAIL")

    if not value:
        raise ValueError("IMD_EMAIL is not set")

    return value


def get_imd_password() -> str:
    """Return IMD account password."""
    value = os.environ.get("IMD_PASSWORD")

    if not value:
        raise ValueError("IMD_PASSWORD is not set")

    return value
