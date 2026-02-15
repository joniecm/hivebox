import unittest
from unittest.mock import Mock, patch

from src.services.temperature_service import (
    CACHE_KEY_LATEST,
    CACHE_TTL_SECONDS,
    TemperatureResponse,
    _refresh_cached_temperature_response,
    get_latest_temperature_response_cached,
)


MODULE_PATH = "src.services.temperature_service"


class TestTemperatureCache(unittest.TestCase):
    """Unit tests for temperature caching helpers."""

    def test_cached_response_returns_direct_when_no_valkey(self):
        response = TemperatureResponse(
            average_temperature=21.5,
            status="Good",
        )
        with patch(f"{MODULE_PATH}.valkey_service", None):
            with patch(
                f"{MODULE_PATH}.get_latest_temperature_response",
                return_value=response,
            ) as mock_latest:
                result = get_latest_temperature_response_cached()

        self.assertEqual(result, response)
        mock_latest.assert_called_once_with()

    def test_cached_response_uses_cache(self):
        valkey = Mock()
        valkey.get_json.return_value = {
            "average_temperature": 18.0,
            "status": "Good",
        }
        valkey.ttl.return_value = 30

        with patch(f"{MODULE_PATH}.valkey_service", valkey):
            with patch(
                f"{MODULE_PATH}.get_latest_temperature_response"
            ) as mock_latest:
                result = get_latest_temperature_response_cached()

        self.assertEqual(result.average_temperature, 18.0)
        self.assertEqual(result.status, "Good")
        mock_latest.assert_not_called()
        valkey.set_json.assert_not_called()

    def test_cached_response_triggers_refresh_on_low_ttl(self):
        valkey = Mock()
        valkey.get_json.return_value = {
            "average_temperature": 19.0,
            "status": "Good",
        }
        valkey.ttl.return_value = 5

        with patch(f"{MODULE_PATH}.valkey_service", valkey):
            with patch(
                f"{MODULE_PATH}."
                "_refresh_cached_temperature_response_async"
            ) as mock_refresh:
                result = get_latest_temperature_response_cached()

        self.assertEqual(result.average_temperature, 19.0)
        mock_refresh.assert_called_once_with()

    def test_cached_response_populates_cache_when_miss(self):
        valkey = Mock()
        valkey.get_json.return_value = None
        response = TemperatureResponse(
            average_temperature=23.0,
            status="Good",
            data_age_seconds=None,
        )

        with patch(f"{MODULE_PATH}.valkey_service", valkey):
            with patch(
                f"{MODULE_PATH}.get_latest_temperature_response",
                return_value=response,
            ):
                result = get_latest_temperature_response_cached()

        self.assertEqual(result, response)
        valkey.set_json.assert_called_once_with(
            CACHE_KEY_LATEST,
            {"average_temperature": 23.0, "status": "Good", "data_age_seconds": None},
            ttl_seconds=CACHE_TTL_SECONDS,
        )

    def test_refresh_cached_temperature_response_skips_when_locked(self):
        valkey = Mock()
        valkey.acquire_lock.return_value = False

        with patch(f"{MODULE_PATH}.valkey_service", valkey):
            with patch(
                f"{MODULE_PATH}.get_latest_temperature_response"
            ) as mock_latest:
                _refresh_cached_temperature_response()

        mock_latest.assert_not_called()
        valkey.release_lock.assert_not_called()

    def test_refresh_cached_temperature_response_sets_cache(self):
        valkey = Mock()
        valkey.acquire_lock.return_value = True
        response = TemperatureResponse(
            average_temperature=25.0,
            status="Good",
            data_age_seconds=None,
        )

        with patch(f"{MODULE_PATH}.valkey_service", valkey):
            with patch(
                f"{MODULE_PATH}.get_latest_temperature_response",
                return_value=response,
            ):
                _refresh_cached_temperature_response()

        valkey.set_json.assert_called_once_with(
            CACHE_KEY_LATEST,
            {"average_temperature": 25.0, "status": "Good", "data_age_seconds": None},
            ttl_seconds=CACHE_TTL_SECONDS,
        )
        valkey.release_lock.assert_called_once_with(
            "temperature:latest:lock"
        )


if __name__ == "__main__":
    unittest.main()
