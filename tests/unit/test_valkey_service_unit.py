import json
import os
import unittest
from unittest.mock import Mock, patch

from src.services.valkey_service import ValkeyService


class TestValkeyService(unittest.TestCase):
    """Unit tests for ValkeyService."""

    def test_from_env_returns_none_when_redis_missing(self):
        with patch("src.services.valkey_service.redis", None):
            self.assertIsNone(ValkeyService.from_env())

    def test_from_env_returns_none_when_host_missing(self):
        with patch("src.services.valkey_service.redis", Mock()):
            with patch.dict(os.environ, {}, clear=True):
                self.assertIsNone(ValkeyService.from_env())

    def test_from_env_builds_client(self):
        mock_redis = Mock()
        mock_client = Mock()
        mock_redis.Redis.return_value = mock_client
        env = {
            "VALKEY_HOST": "valkey",
            "VALKEY_PORT": "6380",
            "VALKEY_DB": "2",
            "VALKEY_PASSWORD": "secret",
            "VALKEY_SSL": "true",
            "VALKEY_TIMEOUT": "3.5",
        }
        with patch("src.services.valkey_service.redis", mock_redis):
            with patch.dict(os.environ, env, clear=True):
                service = ValkeyService.from_env()

        self.assertIsInstance(service, ValkeyService)
        mock_redis.Redis.assert_called_once_with(
            host="valkey",
            port=6380,
            db=2,
            password="secret",
            ssl=True,
            socket_timeout=3.5,
            socket_connect_timeout=3.5,
            decode_responses=True,
        )
        self.assertIs(service.client, mock_client)

    def test_get_json_returns_payload(self):
        client = Mock()
        client.get.return_value = json.dumps({"value": 42})
        service = ValkeyService(client)

        payload = service.get_json("key")

        self.assertEqual(payload, {"value": 42})

    def test_get_json_returns_none_for_invalid_json(self):
        client = Mock()
        client.get.return_value = "not-json"
        service = ValkeyService(client)

        self.assertIsNone(service.get_json("key"))

    def test_set_json_writes_payload(self):
        client = Mock()
        service = ValkeyService(client)

        service.set_json("key", {"value": 1}, ttl_seconds=15)

        client.set.assert_called_once_with(
            "key",
            json.dumps({"value": 1}),
            ex=15,
        )

    def test_ttl_handles_missing_or_negative(self):
        client = Mock()
        service = ValkeyService(client)

        client.ttl.return_value = None
        self.assertIsNone(service.ttl("key"))

        client.ttl.return_value = -1
        self.assertIsNone(service.ttl("key"))

        client.ttl.return_value = 20
        self.assertEqual(service.ttl("key"), 20)

    def test_acquire_lock_returns_boolean(self):
        client = Mock()
        service = ValkeyService(client)

        client.set.return_value = True
        self.assertTrue(service.acquire_lock("lock", ttl_seconds=2))

        client.set.return_value = None
        self.assertFalse(service.acquire_lock("lock", ttl_seconds=2))

    def test_release_lock_calls_delete(self):
        client = Mock()
        service = ValkeyService(client)

        service.release_lock("lock")

        client.delete.assert_called_once_with("lock")


if __name__ == "__main__":
    unittest.main()
