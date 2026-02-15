import json
import logging
import os
from typing import Optional

from src.metrics import CACHE_HIT_TOTAL, CACHE_MISS_TOTAL

try:
    import redis
except ImportError:  # pragma: no cover - fallback when dependency missing
    redis = None


logger = logging.getLogger(__name__)


def _get_bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


class ValkeyService:
    """Service wrapper for Valkey operations."""

    def __init__(self, client: "redis.Redis") -> None:
        self.client = client

    @classmethod
    def from_env(cls) -> Optional["ValkeyService"]:
        if redis is None:
            logger.info("Valkey client not installed; caching disabled.")
            return None

        host = os.getenv("VALKEY_HOST")
        if not host:
            return None

        port = int(os.getenv("VALKEY_PORT", "6379"))
        db = int(os.getenv("VALKEY_DB", "0"))
        password = os.getenv("VALKEY_PASSWORD")
        ssl = _get_bool_env("VALKEY_SSL", False)
        timeout = float(os.getenv("VALKEY_TIMEOUT", "2.0"))

        client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            ssl=ssl,
            socket_timeout=timeout,
            socket_connect_timeout=timeout,
            decode_responses=True,
        )
        return cls(client)

    def get_json(self, key: str) -> Optional[dict]:
        try:
            payload = self.client.get(key)
        except Exception as exc:
            logger.warning("Valkey get failed: %s", exc)
            CACHE_MISS_TOTAL.labels(type="valkey").inc()
            return None

        if not payload:
            CACHE_MISS_TOTAL.labels(type="valkey").inc()
            return None

        try:
            result = json.loads(payload)
            CACHE_HIT_TOTAL.labels(type="valkey").inc()
            return result
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in Valkey for key %s", key)
            CACHE_MISS_TOTAL.labels(type="valkey").inc()
            return None

    def set_json(self, key: str, payload: dict, ttl_seconds: int) -> None:
        try:
            self.client.set(key, json.dumps(payload), ex=ttl_seconds)
        except Exception as exc:
            logger.warning("Valkey set failed: %s", exc)

    def ttl(self, key: str) -> Optional[int]:
        try:
            value = self.client.ttl(key)
        except Exception as exc:
            logger.warning("Valkey ttl failed: %s", exc)
            return None

        if value is None or value < 0:
            return None
        return value

    def acquire_lock(self, key: str, ttl_seconds: int) -> bool:
        try:
            return bool(self.client.set(key, "1", ex=ttl_seconds, nx=True))
        except Exception as exc:
            logger.warning("Valkey lock failed: %s", exc)
            return False

    def release_lock(self, key: str) -> None:
        try:
            self.client.delete(key)
        except Exception as exc:
            logger.warning("Valkey unlock failed: %s", exc)
