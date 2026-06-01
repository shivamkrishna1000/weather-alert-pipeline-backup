from unittest.mock import MagicMock, patch

import pytest

from app.main import main

# ------------------ NO ARGUMENT ------------------


def test_main_no_args(capsys):
    with patch("app.main.load_environment"):
        with patch("sys.argv", ["main.py"]):
            main()

    captured = capsys.readouterr()
    assert "Usage" in captured.out


# ------------------ INVALID MODE ------------------


def test_main_invalid_mode(capsys):
    with patch("app.main.load_environment"), patch(
        "app.main.get_database_url", return_value="db"
    ), patch("app.main.get_connection", return_value=MagicMock()), patch(
        "sys.argv", ["main.py", "invalid"]
    ):

        main()

    captured = capsys.readouterr()
    assert "Invalid mode" in captured.out


# ------------------ WEEKLY ------------------


@patch("app.main.run_weekly_pipeline")
@patch("app.main.get_connection")
@patch("app.main.get_database_url", return_value="db")
@patch("app.main.load_environment")
def test_main_weekly(mock_env, mock_db, mock_conn, mock_weekly):
    connection = MagicMock()
    mock_conn.return_value = connection

    with patch("sys.argv", ["main.py", "weekly"]):
        main()

    mock_weekly.assert_called_once_with(connection, "db")
    connection.close.assert_called_once()


@patch("app.main.run_geocode_pipeline")
@patch("app.main.run_sync_pipeline")
def test_run_weekly_pipeline(
    mock_sync,
    mock_geocode,
):

    from app.main import run_weekly_pipeline

    connection = MagicMock()

    run_weekly_pipeline(
        connection,
        "db_url",
    )

    mock_sync.assert_called_once_with(connection)

    mock_geocode.assert_called_once_with(
        connection,
        "db_url",
        batch_size=100,
    )


# ------------------ DAILY ------------------


@patch("app.main.run_daily_pipeline")
@patch("app.main.get_connection")
@patch("app.main.get_database_url", return_value="db")
@patch("app.main.load_environment")
def test_main_daily(mock_env, mock_db, mock_conn, mock_daily):
    connection = MagicMock()
    mock_conn.return_value = connection

    with patch("sys.argv", ["main.py", "daily"]):
        main()

    mock_daily.assert_called_once_with(connection)
    connection.close.assert_called_once()


@patch("app.main.run_delivery_pipeline")
@patch("app.main.run_weather_pipeline")
def test_run_daily_pipeline_success(
    mock_weather,
    mock_delivery,
):

    from app.main import run_daily_pipeline

    connection = MagicMock()

    run_daily_pipeline(connection)

    mock_weather.assert_called_once_with(connection)

    mock_delivery.assert_called_once_with(connection)


# ------------------ DB URL FAILURE ------------------


@patch("app.main.get_database_url", side_effect=ValueError("fail"))
@patch("app.main.load_environment")
def test_main_db_url_failure(mock_env, mock_db):
    with patch("sys.argv", ["main.py", "weekly"]):
        with pytest.raises(ValueError):
            main()


# ------------------ CONNECTION FAILURE ------------------


@patch("app.main.get_connection", side_effect=RuntimeError("fail"))
@patch("app.main.get_database_url", return_value="db")
@patch("app.main.load_environment")
def test_main_connection_failure(mock_env, mock_db, mock_conn):
    with patch("sys.argv", ["main.py", "weekly"]):
        with pytest.raises(RuntimeError):
            main()


# ------------------ PIPELINE FAILURE ------------------


@patch("app.main.run_daily_pipeline", side_effect=RuntimeError("fail"))
@patch("app.main.get_connection")
@patch("app.main.get_database_url", return_value="db")
@patch("app.main.load_environment")
def test_main_pipeline_failure(mock_env, mock_db, mock_conn, mock_pipeline):
    connection = MagicMock()
    mock_conn.return_value = connection

    with patch("sys.argv", ["main.py", "daily"]):
        with pytest.raises(RuntimeError):
            main()

    # IMPORTANT: finally block
    connection.close.assert_called_once()


# ------------------ DELIVERY RETRY PATH ------------------


@patch("app.main.get_database_url", return_value="db")
@patch("app.main.get_connection")
@patch("app.main.run_weather_pipeline")
def test_run_daily_pipeline_retry_delivery(
    mock_weather,
    mock_get_connection,
    mock_db,
):

    from psycopg2 import OperationalError

    from app.main import run_daily_pipeline

    original_connection = MagicMock()

    retry_connection = MagicMock()

    mock_get_connection.return_value = retry_connection

    with patch("app.main.run_delivery_pipeline") as mock_delivery:

        mock_delivery.side_effect = [
            OperationalError("lost"),
            None,
        ]

        run_daily_pipeline(original_connection)

    assert mock_delivery.call_count == 2

    original_connection.close.assert_called_once()

    retry_connection.close.assert_called_once()
