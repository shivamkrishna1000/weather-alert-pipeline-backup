from unittest.mock import patch

import pytest

from app.config import (
    get_cluster_mode,
    get_database_url,
    get_google_maps_api_key,
    get_imd_api_key,
    get_imd_email,
    get_imd_password,
    get_openweather_api_key,
    get_test_database_url,
    get_wati_api_token,
    get_wati_base_url,
    get_wati_template_name,
    get_zoho_accounts_url,
    get_zoho_api_base,
    get_zoho_client_id,
    get_zoho_client_secret,
    get_zoho_module,
    get_zoho_refresh_token,
    is_debug_mode,
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


def test_get_zoho_client_secret_success():

    with patch.dict("os.environ", {"ZOHO_CLIENT_SECRET": "secret"}):
        assert get_zoho_client_secret() == "secret"


def test_get_zoho_client_secret_missing():

    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError):
            get_zoho_client_secret()


def test_get_zoho_refresh_token_success():

    with patch.dict("os.environ", {"ZOHO_REFRESH_TOKEN": "refresh"}):
        assert get_zoho_refresh_token() == "refresh"


def test_get_zoho_refresh_token_missing():

    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError):
            get_zoho_refresh_token()


def test_get_test_database_url_missing():

    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError):
            get_test_database_url()


def test_get_openweather_api_key_success():

    with patch.dict("os.environ", {"OPENWEATHER_API_KEY": "weather"}):
        assert get_openweather_api_key() == "weather"


def test_get_cluster_mode_valid():

    with patch.dict("os.environ", {"CLUSTER_MODE": "village"}):
        assert get_cluster_mode() == "village"


def test_get_wati_base_url_success():

    with patch.dict("os.environ", {"WATI_BASE_URL": "https://wati.test"}):
        assert get_wati_base_url() == "https://wati.test"


def test_get_wati_base_url_missing():

    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError):
            get_wati_base_url()


def test_get_wati_api_token_success():

    with patch.dict("os.environ", {"WATI_API_TOKEN": "token"}):
        assert get_wati_api_token() == "token"


def test_get_wati_api_token_missing():

    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError):
            get_wati_api_token()


def test_get_wati_template_name_success():

    with patch.dict("os.environ", {"WATI_TEMPLATE_NAME": "weather"}):
        assert get_wati_template_name() == "weather"


def test_get_wati_template_name_missing():

    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError):
            get_wati_template_name()


def test_is_debug_mode_true():

    with patch.dict("os.environ", {"DEBUG_MODE": "true"}):
        assert is_debug_mode() is True


def test_is_debug_mode_false():

    with patch.dict("os.environ", {"DEBUG_MODE": "false"}):
        assert is_debug_mode() is False


def test_get_imd_api_key_success():

    with patch.dict("os.environ", {"IMD_API_KEY": "imd-key"}):
        assert get_imd_api_key() == "imd-key"


def test_get_imd_api_key_missing():

    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError):
            get_imd_api_key()


def test_get_imd_email_success():

    with patch.dict("os.environ", {"IMD_EMAIL": "user@test.com"}):
        assert get_imd_email() == "user@test.com"


def test_get_imd_email_missing():

    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError):
            get_imd_email()


def test_get_imd_password_success():

    with patch.dict("os.environ", {"IMD_PASSWORD": "secret"}):
        assert get_imd_password() == "secret"


def test_get_imd_password_missing():

    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError):
            get_imd_password()
