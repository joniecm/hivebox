import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from typing import Optional

import urllib3
from minio import Minio
from minio.error import S3Error

from src.config import MinioConfig, load_minio_config


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TemperatureRecord:
    average_temperature: float
    timestamp: datetime
    source_hivebox_ids: list[str]


class MinioService:
    """Service wrapper for MinIO operations."""

    def __init__(self, client: Minio, bucket: str, create_bucket: bool = False):
        self.client = client
        self.bucket = bucket
        self.create_bucket = create_bucket
        if create_bucket:
            self._ensure_bucket()

    @classmethod
    def from_env(cls) -> Optional["MinioService"]:
        config = load_minio_config()
        if config is None:
            logger.info("MinIO config not provided; skipping storage.")
            return None
        try:
            return cls.from_config(config)
        except Exception as exc:
            logger.warning("Failed to initialize MinIO client: %s", exc)
            return None

    @classmethod
    def from_config(cls, config: MinioConfig) -> "MinioService":
        timeout = urllib3.util.Timeout(connect=config.timeout, read=config.timeout)
        http_client = urllib3.PoolManager(
            timeout=timeout,
            retries=urllib3.Retry(total=0, connect=0, read=0, redirect=False),
        )
        client = Minio(
            config.endpoint,
            access_key=config.access_key,
            secret_key=config.secret_key,
            secure=config.secure,
            region=config.region,
            http_client=http_client,
        )
        return cls(client, config.bucket, create_bucket=config.create_bucket)

    def ensure_bucket_or_raise(self) -> None:
        """Ensure MinIO is reachable and the bucket exists or can be created."""
        try:
            if self.client.bucket_exists(self.bucket):
                logger.info("MinIO bucket %s is ready.", self.bucket)
                return
            if self.create_bucket:
                self.client.make_bucket(self.bucket)
                logger.info("Created MinIO bucket %s.", self.bucket)
                return
        except (S3Error, Exception) as exc:
            raise RuntimeError("MinIO is not reachable") from exc

        raise RuntimeError(
            "MinIO bucket does not exist and createBucket is disabled"
        )

    def _ensure_bucket(self) -> None:
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except (S3Error, Exception) as exc:
            logger.warning("Failed to ensure MinIO bucket: %s", exc)

    def put_temperature_record(self, record: TemperatureRecord) -> None:
        object_name = record.timestamp.strftime("temperature/%Y/%m/%d/%H%M%S.json")
        payload = {
            "average_temperature": record.average_temperature,
            "timestamp": record.timestamp.isoformat(),
            "source_hivebox_ids": record.source_hivebox_ids,
        }
        data = json.dumps(payload).encode("utf-8")

        try:
            self.client.put_object(
                self.bucket,
                object_name,
                data=BytesIO(data),
                length=len(data),
                content_type="application/json",
            )
        except (S3Error, Exception) as exc:
            logger.warning("Failed to write temperature data to MinIO: %s", exc)

    def put_temperature_records(self, records: list[TemperatureRecord]) -> None:
        for record in records:
            self.put_temperature_record(record)

    def get_latest_record(self) -> Optional[TemperatureRecord]:
        try:
            objects = list(
                self.client.list_objects(
                    self.bucket,
                    prefix="temperature/",
                    recursive=True,
                )
            )
        except (S3Error, Exception) as exc:
            logger.warning("Failed to list temperature records: %s", exc)
            return None

        if not objects:
            return None

        def _sort_key(obj):
            return obj.last_modified or obj.object_name

        latest_object = max(objects, key=_sort_key)

        response = None
        try:
            response = self.client.get_object(self.bucket, latest_object.object_name)
            payload = json.loads(response.read().decode("utf-8"))
        except (S3Error, json.JSONDecodeError, Exception) as exc:
            logger.warning("Failed to read latest temperature record: %s", exc)
            return None
        finally:
            if response is not None:
                response.close()
                response.release_conn()

        timestamp = datetime.fromisoformat(payload["timestamp"])
        return TemperatureRecord(
            average_temperature=float(payload["average_temperature"]),
            timestamp=timestamp,
            source_hivebox_ids=list(payload.get("source_hivebox_ids", [])),
        )


def build_temperature_record(
    average_temperature: float,
    source_hivebox_ids: Optional[list[str]] = None,
) -> TemperatureRecord:
    return TemperatureRecord(
        average_temperature=average_temperature,
        timestamp=datetime.now(timezone.utc),
        source_hivebox_ids=source_hivebox_ids or [],
    )
