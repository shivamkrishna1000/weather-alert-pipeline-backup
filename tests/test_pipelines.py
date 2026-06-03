from unittest.mock import MagicMock, patch

import pytest

from app.constants import ALLOWED_STATUSES
from app.pipelines.delivery_pipeline import run_delivery_pipeline
from app.pipelines.geocode_pipeline import (
    get_coordinates,
    persist_geocoded_result,
    process_record,
    run_geocode_pipeline,
)
from app.pipelines.sync_pipeline import run_sync_pipeline
from app.pipelines.weather_pipeline import run_weather_pipeline

# ------------------ GEOCODE PIPELINE ------------------


def test_process_record_success():
    record = {"id": "1", "attempts": 0}

    with patch(
        "app.pipelines.geocode_pipeline.prepare_address", return_value="addr"
    ), patch("app.pipelines.geocode_pipeline.should_retry", return_value=True), patch(
        "app.pipelines.geocode_pipeline.get_coordinates", return_value=(1.0, 2.0)
    ), patch(
        "app.pipelines.geocode_pipeline.persist_geocoded_result"
    ) as mock_persist:

        result = process_record(None, record)

        assert result is True
        mock_persist.assert_called_once()


def test_process_record_skip_empty_address():
    record = {"id": "1", "attempts": 0}

    with patch("app.pipelines.geocode_pipeline.prepare_address", return_value=None):
        result = process_record(None, record)

        assert result is False


def test_process_record_max_attempts():
    record = {"id": "1", "attempts": 5}

    with patch(
        "app.pipelines.geocode_pipeline.prepare_address", return_value="addr"
    ), patch("app.pipelines.geocode_pipeline.should_retry", return_value=False):

        result = process_record(None, record)

        assert result is False


def test_process_record_no_address():

    with patch("app.pipelines.geocode_pipeline.prepare_address", return_value=None):
        result = process_record(None, {"id": "1"})

        assert result is False


def test_process_record_exception():

    with patch(
        "app.pipelines.geocode_pipeline.prepare_address", return_value="addr"
    ), patch("app.pipelines.geocode_pipeline.should_retry", return_value=True), patch(
        "app.pipelines.geocode_pipeline.get_coordinates",
        side_effect=RuntimeError("fail"),
    ):

        result = process_record(None, {"id": "1", "attempts": 0})

        assert result is False


def test_get_coordinates_cache_hit():

    with patch(
        "app.pipelines.geocode_pipeline.get_from_cache", return_value=(1.0, 2.0)
    ):
        result = get_coordinates(None, "addr", "1")

        assert result == (1.0, 2.0)


def test_get_coordinates_api_success():
    with patch(
        "app.pipelines.geocode_pipeline.get_from_cache", return_value=None
    ), patch(
        "app.pipelines.geocode_pipeline.geocode_address", return_value=(1.0, 2.0)
    ), patch(
        "app.pipelines.geocode_pipeline.insert_into_cache"
    ) as mock_insert:

        result = get_coordinates(None, "addr", "1")

        assert result == (1.0, 2.0)
        mock_insert.assert_called_once()


def test_get_coordinates_value_error():
    with patch(
        "app.pipelines.geocode_pipeline.get_from_cache", return_value=None
    ), patch(
        "app.pipelines.geocode_pipeline.geocode_address",
        side_effect=ValueError("bad"),
    ), patch(
        "app.pipelines.geocode_pipeline.handle_failed_geocode"
    ) as mock_handle:

        with pytest.raises(ValueError):
            get_coordinates(None, "addr", "1")

        mock_handle.assert_called_once_with(None, "1")


def test_get_coordinates_runtime_error():
    with patch(
        "app.pipelines.geocode_pipeline.get_from_cache", return_value=None
    ), patch(
        "app.pipelines.geocode_pipeline.geocode_address",
        side_effect=RuntimeError("fail"),
    ), patch(
        "app.pipelines.geocode_pipeline.handle_failed_geocode"
    ):

        with pytest.raises(RuntimeError):
            get_coordinates(None, "addr", "1")


def test_persist_geocoded_result():
    record = {"id": "1"}

    with patch(
        "app.pipelines.geocode_pipeline.insert_geocoded_record"
    ) as mock_insert, patch(
        "app.pipelines.geocode_pipeline.delete_from_missing"
    ) as mock_delete:

        persist_geocoded_result(None, record, 1.0, 2.0)

        mock_insert.assert_called_once()
        mock_delete.assert_called_once()


def test_run_geocode_pipeline_single_record():
    record = {"id": "1"}

    with patch(
        "app.pipelines.geocode_pipeline.fetch_missing_batch",
        side_effect=[[record], []],
    ), patch(
        "app.pipelines.geocode_pipeline.process_record_parallel",
        return_value=True,
    ), patch(
        "app.pipelines.geocode_pipeline.get_connection",
        return_value=MagicMock(),
    ):

        run_geocode_pipeline(None, database_url="dummy")


def test_get_coordinates_value_error_triggers_retry():
    with patch(
        "app.pipelines.geocode_pipeline.get_from_cache", return_value=None
    ), patch(
        "app.pipelines.geocode_pipeline.geocode_address",
        side_effect=ValueError("bad"),
    ), patch(
        "app.pipelines.geocode_pipeline.increment_attempt"
    ) as mock_increment:

        with pytest.raises(ValueError):
            get_coordinates(None, "addr", "1")

        mock_increment.assert_called_once_with(None, "1")


# ------------------ SYNC PIPELINE ------------------


@patch("app.pipelines.sync_pipeline.delete_greenhouse")
@patch("app.pipelines.sync_pipeline.create_tables")
@patch("app.pipelines.sync_pipeline.fetch_all_greenhouse_data")
@patch("app.pipelines.sync_pipeline.process_greenhouse_records")
@patch("app.pipelines.sync_pipeline.insert_greenhouses")
@patch("app.pipelines.sync_pipeline.insert_missing_location")
@patch("app.pipelines.sync_pipeline.update_last_sync_time")
def test_run_sync_pipeline_success(
    mock_update,
    mock_insert_missing,
    mock_insert,
    mock_process,
    mock_fetch,
    mock_create,
    mock_delete,
):
    mock_fetch.return_value = [
        {
            "Modified_Time": "2024-01-01T00:00:00",
            "id": "1",
            "Current_GH_Status": list(ALLOWED_STATUSES)[0],
        }
    ]
    mock_process.return_value = ([], [])

    run_sync_pipeline(None)

    mock_create.assert_called_once()
    mock_fetch.assert_called_once()
    mock_insert.assert_called_once()
    mock_insert_missing.assert_called_once()
    mock_update.assert_called_once()


@patch("app.pipelines.sync_pipeline.fetch_all_greenhouse_data", return_value=[])
@patch("app.pipelines.sync_pipeline.create_tables")
def test_sync_pipeline_no_records(mock_create, mock_fetch):

    run_sync_pipeline(None)

    mock_create.assert_called_once()


@patch("app.pipelines.sync_pipeline.insert_greenhouses")
@patch("app.pipelines.sync_pipeline.insert_missing_location")
@patch("app.pipelines.sync_pipeline.process_greenhouse_records", return_value=([], []))
@patch("app.pipelines.sync_pipeline.delete_greenhouse")
@patch("app.pipelines.sync_pipeline.fetch_all_greenhouse_data")
@patch("app.pipelines.sync_pipeline.create_tables")
def test_sync_pipeline_invalid_records_deleted(
    mock_create,
    mock_fetch,
    mock_delete,
    mock_process,
    mock_insert_missing,
    mock_insert,
):

    mock_fetch.return_value = [{"id": "1", "Current_GH_Status": "invalid"}]

    run_sync_pipeline(None)

    mock_delete.assert_called_once_with(None, "1")


# ------------------ WEATHER PIPELINE ------------------


@patch("app.pipelines.weather_pipeline.get_connection", return_value=MagicMock())
@patch("app.pipelines.weather_pipeline.get_database_url", return_value="dummy")
def test_weather_pipeline_cache_hit(mock_db_url, mock_conn):
    connection = object()

    clusters = [{"cluster_key": "A", "latitude": 1, "longitude": 2}]

    with patch(
        "app.pipelines.weather_pipeline.fetch_clusters", return_value=clusters
    ), patch(
        "app.pipelines.weather_pipeline.get_cached_weather",
        return_value={"fetched_at": "now"},
    ), patch(
        "app.pipelines.weather_pipeline.is_cache_fresh", return_value=True
    ), patch(
        "app.pipelines.weather_pipeline.process_cluster_parallel",
        return_value=False,
    ) as mock_process:

        run_weather_pipeline(connection)

        mock_process.assert_called_once()


@patch("app.pipelines.weather_pipeline.get_connection", return_value=MagicMock())
@patch("app.pipelines.weather_pipeline.get_database_url", return_value="dummy")
def test_weather_pipeline_fetch_and_store(mock_db_url, mock_conn):
    connection = MagicMock()

    clusters = [{"cluster_key": "A", "latitude": 1, "longitude": 2}]

    with patch(
        "app.pipelines.weather_pipeline.fetch_clusters",
        return_value=clusters,
    ), patch(
        "app.pipelines.weather_pipeline.process_cluster_parallel",
        return_value=True,
    ):

        run_weather_pipeline(connection)

        assert True


@patch("app.pipelines.weather_pipeline.get_connection", return_value=MagicMock())
@patch("app.pipelines.weather_pipeline.get_database_url", return_value="dummy")
def test_weather_pipeline_api_failure(mock_db_url, mock_conn):
    clusters = [{"cluster_key": "A", "latitude": 1, "longitude": 2}]

    with patch(
        "app.pipelines.weather_pipeline.fetch_clusters",
        return_value=clusters,
    ), patch(
        "app.pipelines.weather_pipeline.process_cluster_parallel",
        side_effect=RuntimeError("fail"),
    ):

        run_weather_pipeline(MagicMock())

        assert True


def test_filter_pilot_clusters_no_villages():

    from app.pipelines.weather_pipeline import filter_pilot_clusters

    with patch(
        "app.pipelines.weather_pipeline.is_pilot_mode",
        return_value=True,
    ), patch(
        "app.pipelines.weather_pipeline.get_pilot_villages",
        return_value=set(),
    ):

        result = filter_pilot_clusters([])

    assert result == []


def test_filter_pilot_clusters_match():

    from app.pipelines.weather_pipeline import filter_pilot_clusters

    clusters = [
        {
            "cluster_key": "A",
            "members": [{"village": "Village1"}],
        }
    ]

    with patch(
        "app.pipelines.weather_pipeline.is_pilot_mode",
        return_value=True,
    ), patch(
        "app.pipelines.weather_pipeline.get_pilot_villages",
        return_value={"VILLAGE1"},
    ):

        result = filter_pilot_clusters(clusters)

    assert len(result) == 1


def test_fetch_and_prepare_weather():

    from app.pipelines.weather_pipeline import fetch_and_prepare_weather

    cluster = {
        "cluster_key": "A",
        "latitude": 1,
        "longitude": 2,
    }

    with patch(
        "app.pipelines.weather_pipeline.build_weather_payload",
        return_value={"today_forecast": {}},
    ), patch(
        "app.pipelines.weather_pipeline.generate_advisories",
        return_value="Rain alert",
    ):

        result = fetch_and_prepare_weather(cluster)

    assert result["advisories"] == "Rain alert"


def test_generate_and_store_advisories():

    from app.pipelines.weather_pipeline import generate_and_store_advisories

    connection = MagicMock()

    cluster = {
        "cluster_key": "A",
        "members": [
            {
                "id": "1",
                "name": "GH1",
            },
        ],
    }

    with patch(
        "app.pipelines.weather_pipeline.advisory_already_sent",
        return_value=False,
    ), patch(
        "app.pipelines.weather_pipeline.insert_advisory_log",
    ) as mock_insert:

        generate_and_store_advisories(
            connection,
            cluster,
            {
                "current": "",
                "today": "Rain alert",
                "tomorrow": "",
                "day3": "",
            },
        )

    mock_insert.assert_called_once()


def test_generate_and_store_advisories_skip_existing():

    from app.pipelines.weather_pipeline import generate_and_store_advisories

    connection = MagicMock()

    cluster = {
        "cluster_key": "A",
        "members": [
            {
                "id": "1",
                "name": "GH1",
            },
        ],
    }

    with patch(
        "app.pipelines.weather_pipeline.advisory_already_sent",
        return_value=True,
    ), patch(
        "app.pipelines.weather_pipeline.insert_advisory_log",
    ) as mock_insert:

        generate_and_store_advisories(
            connection,
            cluster,
            {
                "current": "",
                "today": "Rain alert",
                "tomorrow": "",
                "day3": "",
            },
        )

    mock_insert.assert_not_called()


def test_update_weather_storage():

    from app.pipelines.weather_pipeline import update_weather_storage

    connection = MagicMock()

    cluster = {"cluster_key": "A"}

    with patch(
        "app.pipelines.weather_pipeline.upsert_weather_cache",
    ) as mock_cache, patch(
        "app.pipelines.weather_pipeline.insert_weather_history",
    ) as mock_history:

        update_weather_storage(
            connection,
            cluster,
        )

    mock_cache.assert_called_once()
    mock_history.assert_called_once()


def test_process_cluster_skip():

    from app.pipelines.weather_pipeline import process_cluster

    with patch(
        "app.pipelines.weather_pipeline.should_skip_cluster",
        return_value=True,
    ):

        result = process_cluster(
            MagicMock(),
            {"cluster_key": "A"},
        )

    assert result is False


def test_process_cluster_success():

    from app.pipelines.weather_pipeline import process_cluster

    cluster = {
        "cluster_key": "A",
        "members": [],
    }

    enriched = {
        "advisories": "Rain alert",
    }

    with patch(
        "app.pipelines.weather_pipeline.should_skip_cluster",
        return_value=False,
    ), patch(
        "app.pipelines.weather_pipeline.fetch_and_prepare_weather",
        return_value=enriched,
    ), patch(
        "app.pipelines.weather_pipeline.generate_and_store_advisories",
    ) as mock_adv, patch(
        "app.pipelines.weather_pipeline.update_weather_storage",
    ) as mock_store:

        result = process_cluster(
            MagicMock(),
            cluster,
        )

    assert result is True
    mock_adv.assert_called_once()
    mock_store.assert_called_once()


def test_process_cluster_parallel():

    from app.pipelines.weather_pipeline import process_cluster_parallel

    mock_connection = MagicMock()

    with patch(
        "app.pipelines.weather_pipeline.get_connection",
        return_value=mock_connection,
    ), patch(
        "app.pipelines.weather_pipeline.process_cluster",
        return_value=True,
    ):

        result = process_cluster_parallel(
            {"cluster_key": "A"},
            "db_url",
        )

    assert result is True
    mock_connection.close.assert_called_once()


# ------------------ DELIVERY PIPELINE ------------------


@patch("app.pipelines.delivery_pipeline.fetch_pending_advisories", return_value=[])
def test_delivery_no_records(mock_fetch):
    connection = MagicMock()

    run_delivery_pipeline(connection)

    mock_fetch.assert_called_once()


@patch("app.pipelines.delivery_pipeline.mark_advisories_as_sent")
@patch("app.pipelines.delivery_pipeline.send_whatsapp_message", return_value=True)
@patch("app.pipelines.delivery_pipeline.group_advisories_by_farmer")
@patch("app.pipelines.delivery_pipeline.fetch_pending_advisories")
def test_delivery_success(
    mock_fetch,
    mock_group,
    mock_send,
    mock_mark,
):
    connection = MagicMock()

    mock_fetch.return_value = ["dummy"]

    mock_group.return_value = {
        "999": {
            "farmer_name": "Ravi",
            "advisories": [
                {
                    "greenhouse": "GH1",
                    "current": "",
                    "today": "Rain alert",
                    "tomorrow": "",
                    "day3": "",
                }
            ],
            "ids": [1],
        }
    }

    run_delivery_pipeline(connection)

    mock_send.assert_called_once()
    mock_mark.assert_called_once()


@patch("app.pipelines.delivery_pipeline.mark_advisories_as_sent")
@patch("app.pipelines.delivery_pipeline.send_whatsapp_message", return_value=False)
@patch("app.pipelines.delivery_pipeline.group_advisories_by_farmer")
@patch("app.pipelines.delivery_pipeline.fetch_pending_advisories")
def test_delivery_partial_failure(
    mock_fetch,
    mock_group,
    mock_send,
    mock_mark,
):
    connection = MagicMock()

    mock_fetch.return_value = ["dummy"]

    mock_group.return_value = {
        "999": {
            "farmer_name": "Ravi",
            "advisories": [
                {
                    "greenhouse": "GH1",
                    "current": "",
                    "today": "Rain alert",
                    "tomorrow": "",
                    "day3": "",
                }
            ],
            "ids": [1],
        }
    }

    run_delivery_pipeline(connection)

    mock_send.assert_called_once()
    mock_mark.assert_not_called()
