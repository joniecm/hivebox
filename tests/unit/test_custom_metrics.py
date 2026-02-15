"""Unit tests for custom Prometheus metrics."""

import unittest
from unittest.mock import MagicMock, patch

from src.metrics import (
    CACHE_HIT_TOTAL,
    CACHE_MISS_TOTAL,
    STORAGE_WRITE_OPERATIONS_TOTAL,
    TEMPERATURE_DATA_AGE_SECONDS,
    TEMPERATURE_REQUESTS_TOTAL,
)
from src.services.minio_service import MinioService, TemperatureRecord
from src.services.valkey_service import ValkeyService
from datetime import datetime, timezone


class TestCacheMetrics(unittest.TestCase):
    """Test cache metrics in ValkeyService."""

    def test_cache_hit_increments_on_success(self):
        """Test that cache hit metric increments on successful cache lookup."""
        mock_client = MagicMock()
        mock_client.get.return_value = '{"test": "data"}'
        
        service = ValkeyService(mock_client)
        
        # Record initial value
        initial_value = CACHE_HIT_TOTAL.labels(type="valkey")._value.get()
        
        # Perform operation
        result = service.get_json("test_key")
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result, {"test": "data"})
        final_value = CACHE_HIT_TOTAL.labels(type="valkey")._value.get()
        self.assertEqual(final_value, initial_value + 1)

    def test_cache_miss_increments_on_empty_result(self):
        """Test that cache miss metric increments when key not found."""
        mock_client = MagicMock()
        mock_client.get.return_value = None
        
        service = ValkeyService(mock_client)
        
        # Record initial value
        initial_value = CACHE_MISS_TOTAL.labels(type="valkey")._value.get()
        
        # Perform operation
        result = service.get_json("test_key")
        
        # Assert
        self.assertIsNone(result)
        final_value = CACHE_MISS_TOTAL.labels(type="valkey")._value.get()
        self.assertEqual(final_value, initial_value + 1)

    def test_cache_miss_increments_on_exception(self):
        """Test that cache miss metric increments when exception occurs."""
        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("Connection error")
        
        service = ValkeyService(mock_client)
        
        # Record initial value
        initial_value = CACHE_MISS_TOTAL.labels(type="valkey")._value.get()
        
        # Perform operation
        result = service.get_json("test_key")
        
        # Assert
        self.assertIsNone(result)
        final_value = CACHE_MISS_TOTAL.labels(type="valkey")._value.get()
        self.assertEqual(final_value, initial_value + 1)


class TestStorageMetrics(unittest.TestCase):
    """Test storage metrics in MinioService."""

    def test_storage_write_success_increments(self):
        """Test that storage write success metric increments."""
        mock_client = MagicMock()
        mock_client.put_object.return_value = None
        
        service = MinioService(mock_client, "test-bucket")
        
        # Record initial value
        initial_value = STORAGE_WRITE_OPERATIONS_TOTAL.labels(
            type="minio", status="success"
        )._value.get()
        
        # Perform operation
        record = TemperatureRecord(
            average_temperature=22.5,
            timestamp=datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            source_hivebox_ids=["box-1"],
        )
        service.put_temperature_record(record)
        
        # Assert
        final_value = STORAGE_WRITE_OPERATIONS_TOTAL.labels(
            type="minio", status="success"
        )._value.get()
        self.assertEqual(final_value, initial_value + 1)

    def test_storage_write_failure_increments(self):
        """Test that storage write failure metric increments."""
        mock_client = MagicMock()
        mock_client.put_object.side_effect = Exception("S3 error")
        
        service = MinioService(mock_client, "test-bucket")
        
        # Record initial value
        initial_value = STORAGE_WRITE_OPERATIONS_TOTAL.labels(
            type="minio", status="failed"
        )._value.get()
        
        # Perform operation
        record = TemperatureRecord(
            average_temperature=22.5,
            timestamp=datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            source_hivebox_ids=["box-1"],
        )
        service.put_temperature_record(record)
        
        # Assert
        final_value = STORAGE_WRITE_OPERATIONS_TOTAL.labels(
            type="minio", status="failed"
        )._value.get()
        self.assertEqual(final_value, initial_value + 1)


class TestTemperatureEndpointMetrics(unittest.TestCase):
    """Test temperature endpoint metrics."""

    @patch("src.routes.temperature.get_latest_temperature_response_cached")
    def test_temperature_request_success_increments(self, mock_get_temp):
        """Test that temperature success metric increments."""
        from src.app import app
        from src.services.temperature_service import TemperatureResponse

        mock_get_temp.return_value = TemperatureResponse(
            average_temperature=22.5,
            status="Good",
            data_age_seconds=10.0,
        )
        
        # Record initial value
        initial_value = TEMPERATURE_REQUESTS_TOTAL.labels(
            status="success"
        )._value.get()
        
        # Perform operation
        client = app.test_client()
        response = client.get("/temperature")
        
        # Assert
        self.assertEqual(response.status_code, 200)
        final_value = TEMPERATURE_REQUESTS_TOTAL.labels(
            status="success"
        )._value.get()
        self.assertEqual(final_value, initial_value + 1)

    @patch("src.routes.temperature.get_latest_temperature_response_cached")
    def test_temperature_request_no_data_increments(self, mock_get_temp):
        """Test that temperature no_data metric increments."""
        from src.app import app

        mock_get_temp.return_value = None
        
        # Record initial value
        initial_value = TEMPERATURE_REQUESTS_TOTAL.labels(
            status="no_data"
        )._value.get()
        
        # Perform operation
        client = app.test_client()
        response = client.get("/temperature")
        
        # Assert
        self.assertEqual(response.status_code, 503)
        final_value = TEMPERATURE_REQUESTS_TOTAL.labels(
            status="no_data"
        )._value.get()
        self.assertEqual(final_value, initial_value + 1)

    @patch("src.routes.temperature.get_latest_temperature_response_cached")
    def test_temperature_data_age_gauge_updated(self, mock_get_temp):
        """Test that temperature data age gauge is updated."""
        from src.app import app
        from src.services.temperature_service import TemperatureResponse

        mock_get_temp.return_value = TemperatureResponse(
            average_temperature=22.5,
            status="Good",
            data_age_seconds=45.5,
        )
        
        # Perform operation
        client = app.test_client()
        response = client.get("/temperature")
        
        # Assert
        self.assertEqual(response.status_code, 200)
        gauge_value = TEMPERATURE_DATA_AGE_SECONDS._value.get()
        self.assertEqual(gauge_value, 45.5)


class TestMetricsEndpoint(unittest.TestCase):
    """Test that custom metrics are exposed via /metrics endpoint."""

    def test_metrics_endpoint_includes_custom_metrics(self):
        """Test that /metrics endpoint includes custom metrics."""
        from src.app import app

        client = app.test_client()
        response = client.get("/metrics")
        body = response.data.decode("utf-8")
        
        # Check that all custom metrics are present
        self.assertIn("cache_hit_total", body)
        self.assertIn("cache_miss_total", body)
        self.assertIn("storage_write_operations_total", body)
        self.assertIn("temperature_requests_total", body)
        self.assertIn("temperature_data_age_seconds", body)


if __name__ == "__main__":
    unittest.main()
