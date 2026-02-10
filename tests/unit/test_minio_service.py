import json
import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from src.config import MinioConfig
from src.services.minio_service import (
    MinioService,
    TemperatureRecord,
    build_temperature_record,
)


class TestMinioService(unittest.TestCase):
    """Test cases for MinioService."""

    def test_from_env_missing_config(self):
        """Return None when MinIO config is not provided."""
        with patch("src.services.minio_service.load_minio_config", return_value=None):
            self.assertIsNone(MinioService.from_env())

    def test_from_config_builds_client(self):
        """Create MinIO client using provided config."""
        config = MinioConfig(
            endpoint="minio:9000",
            access_key="access",
            secret_key="secret",
            bucket="temps",
            secure=False,
            region="us-east-1",
            create_bucket=False,
        )
        with patch("src.services.minio_service.Minio") as minio_cls:
            client = minio_cls.return_value
            service = MinioService.from_config(config)

        minio_cls.assert_called_once_with(
            "minio:9000",
            access_key="access",
            secret_key="secret",
            secure=False,
            region="us-east-1",
        )
        self.assertIs(service.client, client)
        self.assertEqual(service.bucket, "temps")

    def test_init_create_bucket_when_missing(self):
        """Create bucket when it does not exist and create_bucket is True."""
        client = Mock()
        client.bucket_exists.return_value = False

        MinioService(client, "temps", create_bucket=True)

        client.make_bucket.assert_called_once_with("temps")

    def test_init_does_not_create_bucket_if_exists(self):
        """Do not create bucket if it already exists."""
        client = Mock()
        client.bucket_exists.return_value = True

        MinioService(client, "temps", create_bucket=True)

        client.make_bucket.assert_not_called()

    def test_put_temperature_record_uploads_object(self):
        """Upload temperature record with expected object name and content."""
        client = Mock()
        service = MinioService(client, "temps")
        record = TemperatureRecord(
            average_temperature=22.5,
            timestamp=datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            source_hivebox_ids=["box-1", "box-2"],
        )

        service.put_temperature_record(record)

        client.put_object.assert_called_once()
        args, kwargs = client.put_object.call_args
        self.assertEqual(args[0], "temps")
        self.assertEqual(args[1], "temperature/2026/01/01/120000.json")
        payload = json.loads(kwargs["data"].getvalue().decode("utf-8"))
        self.assertEqual(payload["average_temperature"], 22.5)
        self.assertEqual(payload["source_hivebox_ids"], ["box-1", "box-2"])
        self.assertEqual(kwargs["length"], len(kwargs["data"].getvalue()))
        self.assertEqual(kwargs["content_type"], "application/json")

    def test_put_temperature_records_calls_single_put(self):
        """Batch upload delegates to single-record method."""
        client = Mock()
        service = MinioService(client, "temps")
        records = [
            TemperatureRecord(
                average_temperature=20.0,
                timestamp=datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
                source_hivebox_ids=["box-1"],
            ),
            TemperatureRecord(
                average_temperature=21.0,
                timestamp=datetime(2026, 1, 1, 11, 0, 0, tzinfo=timezone.utc),
                source_hivebox_ids=["box-2"],
            ),
        ]

        with patch.object(service, "put_temperature_record") as put_record:
            service.put_temperature_records(records)

        self.assertEqual(put_record.call_count, 2)

    def test_get_latest_record_returns_latest(self):
        """Retrieve the latest record from MinIO."""
        client = Mock()
        service = MinioService(client, "temps")

        older = Mock()
        older.object_name = "temperature/2026/01/01/090000.json"
        older.last_modified = datetime(2026, 1, 1, 9, 0, 0, tzinfo=timezone.utc)

        newer = Mock()
        newer.object_name = "temperature/2026/01/01/120000.json"
        newer.last_modified = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        client.list_objects.return_value = [older, newer]

        response = Mock()
        response.read.return_value = json.dumps({
            "average_temperature": 22.5,
            "timestamp": "2026-01-01T12:00:00+00:00",
            "source_hivebox_ids": ["box-1", "box-2"],
        }).encode("utf-8")
        client.get_object.return_value = response

        record = service.get_latest_record()

        client.get_object.assert_called_once_with("temps", newer.object_name)
        self.assertIsNotNone(record)
        self.assertEqual(record.average_temperature, 22.5)
        self.assertEqual(record.source_hivebox_ids, ["box-1", "box-2"])


class TestBuildTemperatureRecord(unittest.TestCase):
    """Test cases for build_temperature_record helper."""

    def test_build_temperature_record_uses_utc(self):
        """Ensure record timestamps are timezone-aware and UTC."""
        record = build_temperature_record(18.25, ["box-1"])

        self.assertEqual(record.average_temperature, 18.25)
        self.assertIsNotNone(record.timestamp.tzinfo)
        self.assertEqual(record.timestamp.tzinfo, timezone.utc)
        self.assertEqual(record.source_hivebox_ids, ["box-1"])


if __name__ == "__main__":
    unittest.main()
