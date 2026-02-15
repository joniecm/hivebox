import json
import unittest
from unittest.mock import patch

from src.app import app


class TestStoreEndpoint(unittest.TestCase):
    """Test cases for the /store endpoint."""

    def setUp(self):
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    @patch("src.routes.store.flush_temperature_records")
    def test_store_returns_flushed_count(self, mock_flush):
        mock_flush.return_value = (3, True)

        response = self.client.post("/store")

        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.data)
        self.assertEqual(payload["flushed"], 3)

    @patch("src.routes.store.flush_temperature_records")
    def test_store_returns_503_when_minio_missing(self, mock_flush):
        mock_flush.return_value = (0, False)

        response = self.client.post("/store")

        self.assertEqual(response.status_code, 503)
        payload = json.loads(response.data)
        self.assertIn("error", payload)
        self.assertIn("message", payload)


if __name__ == "__main__":
    unittest.main()
