import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MinioConfig:
    endpoint: str
    access_key: str
    secret_key: str
    bucket: str
    secure: bool = True
    region: Optional[str] = None
    create_bucket: bool = False
    timeout: float = 5.0


def _get_bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def load_minio_config() -> Optional[MinioConfig]:
    endpoint = os.getenv("MINIO_ENDPOINT")
    access_key = os.getenv("MINIO_ACCESS_KEY")
    secret_key = os.getenv("MINIO_SECRET_KEY")
    bucket = os.getenv("MINIO_BUCKET")

    if not all([endpoint, access_key, secret_key, bucket]):
        return None

    secure = _get_bool_env("MINIO_SECURE", True)
    region = os.getenv("MINIO_REGION")
    create_bucket = _get_bool_env("MINIO_CREATE_BUCKET", False)
    timeout = float(os.getenv("MINIO_TIMEOUT", "5.0"))

    return MinioConfig(
        endpoint=endpoint,
        access_key=access_key,
        secret_key=secret_key,
        bucket=bucket,
        secure=secure,
        region=region,
        create_bucket=create_bucket,
        timeout=timeout,
    )
