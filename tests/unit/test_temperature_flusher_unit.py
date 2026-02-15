import unittest
from unittest.mock import Mock, patch

import src.background.temperature_flusher as flusher


class TestTemperatureFlusher(unittest.TestCase):
    """Unit tests for the temperature flusher."""

    def setUp(self):
        flusher._minio_service = None
        flusher._temperature_records = []
        flusher._last_flush_time = None

    def test_flush_temperature_records_returns_false_when_no_minio(self):
        with patch(
            "src.background.temperature_flusher.MinioService.from_env",
            return_value=None,
        ):
            flushed, success = flusher.flush_temperature_records()

        self.assertEqual(flushed, 0)
        self.assertFalse(success)

    def test_collect_and_flush_records(self):
        flusher._minio_service = Mock()

        record_one = flusher.collect_temperature_record(20.5, ["box-1"])
        record_two = flusher.collect_temperature_record(21.5, ["box-2"])

        flushed = flusher._flush_collected_records()

        self.assertEqual(flushed, 2)
        flusher._minio_service.put_temperature_records.assert_called_once()
        args, _ = flusher._minio_service.put_temperature_records.call_args
        self.assertEqual(args[0], [record_one, record_two])
        self.assertEqual(flusher._temperature_records, [])
        self.assertIsNotNone(flusher._last_flush_time)

    def test_flush_collected_records_returns_zero_when_empty(self):
        flusher._minio_service = Mock()

        flushed = flusher._flush_collected_records()

        self.assertEqual(flushed, 0)
        flusher._minio_service.put_temperature_records.assert_not_called()


if __name__ == "__main__":
    unittest.main()
