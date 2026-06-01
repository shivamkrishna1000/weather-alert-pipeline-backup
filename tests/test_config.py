from unittest.mock import patch

import pytest

from app.config import (
    get_cluster_mode,
    get_database_url,
    get_google_maps_api_key,
    get_openweather_api_key,
    get_test_database_url,
    get_zoho_accounts_url,
    get_zoho_api_base,
    get_zoho_client_id,
    get_zoho_module,
    load_environment,
)


def test_load_environment_calls_dotenv():

    with patch("app.config.load_dotenv") as mock_load:
        load_environment()
        mock_load.assert_called_once()


def test_get_database_url_missing(monkeypatch):

    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValueError):
        get_database_url()


def test_get_google_maps_api_key_missing(monkeypatch):

    monkeypatch.delenv("GOOGLE_MAPS_API_KEY", raising=False)

    with pytest.raises(ValueError):
        get_google_maps_api_key()


def test_get_zoho_client_id_success():

    with patch.dict("os.environ", {"ZOHO_CLIENT_ID": "abc"}):
        assert get_zoho_client_id() == "abc"


def test_get_zoho_client_id_missing():

    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError):
            get_zoho_client_id()


def test_get_google_maps_api_key():

    with patch.dict("os.environ", {"GOOGLE_MAPS_API_KEY": "key"}):
        assert get_google_maps_api_key() == "key"


def test_get_zoho_accounts_url_default():

    with patch.dict("os.environ", {}, clear=True):
        assert get_zoho_accounts_url() == "https://accounts.zoho.com"


def test_get_zoho_api_base_default():

    with patch.dict("os.environ", {}, clear=True):
        assert get_zoho_api_base() == "https://www.zohoapis.com"


def test_get_zoho_module_default():

    with patch.dict("os.environ", {}, clear=True):
        assert get_zoho_module() == "Greenhouse"


def test_get_openweather_api_key_missing():

    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError):
            get_openweather_api_key()


def test_get_cluster_mode_invalid():
    with patch.dict("os.environ", {"CLUSTER_MODE": "invalid"}):
        with pytest.raises(ValueError):
            get_cluster_mode()


def test_get_test_database_url_success():
    with patch.dict("os.environ", {"TEST_DATABASE_URL": "test_db"}):
        assert get_test_database_url() == "test_db"
