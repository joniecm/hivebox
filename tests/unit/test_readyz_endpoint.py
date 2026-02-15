"""Unit tests for the /readyz endpoint."""
import unittest
from unittest.mock import patch

from src.app import app
from src.routes.readyz import (
    check_sensebox_accessibility,
    get_cache_age_seconds,
)


class TestReadyzEndpoint(unittest.TestCase):
    """Test cases for the /readyz endpoint."""

    def setUp(self):
        """Set up test client."""
        self.app = app
        self.app.testing = True
        self.client = self.app.test_client()

    @patch("src.routes.readyz.check_sensebox_accessibility")
    @patch("src.routes.readyz.get_cache_age_seconds")
    def test_readyz_returns_200_when_all_boxes_accessible(
        self, mock_cache_age, mock_check
    ):
        """Test that /readyz returns 200 when all senseBoxes are accessible."""
        mock_check.return_value = (3, 3)  # all accessible
        mock_cache_age.return_value = 30  # 30 seconds old

        response = self.client.get("/readyz")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "ready")
        self.assertEqual(data["sensebox"]["accessible"], 3)
        self.assertEqual(data["sensebox"]["total"], 3)

    @patch("src.routes.readyz.check_sensebox_accessibility")
    @patch("src.routes.readyz.get_cache_age_seconds")
    def test_readyz_returns_200_when_half_accessible_cache_fresh(
        self, mock_cache_age, mock_check
    ):
        """Test /readyz returns 200 when 50% accessible, cache fresh."""
        # 1 accessible, 2 inaccessible (not > 50%)
        mock_check.return_value = (1, 3)
        mock_cache_age.return_value = 60  # 1 minute old

        response = self.client.get("/readyz")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "ready")

    @patch("src.routes.readyz.check_sensebox_accessibility")
    @patch("src.routes.readyz.get_cache_age_seconds")
    def test_readyz_returns_200_when_many_inaccessible_but_cache_fresh(
        self, mock_cache_age, mock_check
    ):
        """Test /readyz returns 200 when >50% inaccessible, cache fresh."""
        mock_check.return_value = (0, 3)  # all inaccessible
        mock_cache_age.return_value = 60  # 1 minute old (< 5 minutes)

        response = self.client.get("/readyz")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "ready")

    @patch("src.routes.readyz.check_sensebox_accessibility")
    @patch("src.routes.readyz.get_cache_age_seconds")
    def test_readyz_returns_200_when_cache_old_but_boxes_accessible(
        self, mock_cache_age, mock_check
    ):
        """Test /readyz returns 200 when cache old, boxes accessible."""
        mock_check.return_value = (3, 3)  # all accessible
        mock_cache_age.return_value = 400  # 6+ minutes old

        response = self.client.get("/readyz")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "ready")

    @patch("src.routes.readyz.check_sensebox_accessibility")
    @patch("src.routes.readyz.get_cache_age_seconds")
    def test_readyz_returns_503_when_both_conditions_met(
        self, mock_cache_age, mock_check
    ):
        """Test /readyz returns 503 when >50% inaccessible AND old."""
        mock_check.return_value = (0, 3)  # all inaccessible (3 > 50%)
        mock_cache_age.return_value = 400  # 6+ minutes old

        response = self.client.get("/readyz")
        self.assertEqual(response.status_code, 503)
        data = response.get_json()
        self.assertEqual(data["status"], "not_ready")
        self.assertIn("reason", data)

    @patch("src.routes.readyz.check_sensebox_accessibility")
    @patch("src.routes.readyz.get_cache_age_seconds")
    def test_readyz_returns_503_with_2_of_3_inaccessible_and_old_cache(
        self, mock_cache_age, mock_check
    ):
        """Test /readyz returns 503 when 2/3 inaccessible, cache old."""
        mock_check.return_value = (1, 3)  # 1 accessible, 2 inaccessible
        mock_cache_age.return_value = 400  # 6+ minutes old

        response = self.client.get("/readyz")
        # 2 inaccessible out of 3: 2 > (3 // 2) = 2 > 1, so > 50%
        # But wait: 2/3 = 66.6%, which is indeed > 50%
        # threshold = 3 // 2 = 1, inaccessible = 2, 2 > 1 is True
        self.assertEqual(response.status_code, 503)
        data = response.get_json()
        self.assertEqual(data["status"], "not_ready")

    @patch("src.routes.readyz.check_sensebox_accessibility")
    @patch("src.routes.readyz.get_cache_age_seconds")
    def test_readyz_cache_none_treated_as_fresh(
        self, mock_cache_age, mock_check
    ):
        """Test that /readyz returns 200 when cache_age is None (no cache)."""
        mock_check.return_value = (0, 3)  # all inaccessible
        mock_cache_age.return_value = None  # no cache

        response = self.client.get("/readyz")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "ready")
        self.assertIsNone(data["cache"]["age_seconds"])


class TestCheckSenseboxAccessibility(unittest.TestCase):
    """Test cases for check_sensebox_accessibility helper."""

    @patch("src.routes.readyz.sensebox_service._get_sensebox_data")
    def test_all_accessible(self, mock_get_data):
        """Test when all senseBoxes are accessible."""
        mock_get_data.return_value = {"sensors": []}

        accessible, total = check_sensebox_accessibility()
        self.assertEqual(accessible, 3)
        self.assertEqual(total, 3)

    @patch("src.routes.readyz.sensebox_service._get_sensebox_data")
    def test_none_accessible(self, mock_get_data):
        """Test when no senseBoxes are accessible."""
        mock_get_data.return_value = None

        accessible, total = check_sensebox_accessibility()
        self.assertEqual(accessible, 0)
        self.assertEqual(total, 3)

    @patch("src.routes.readyz.sensebox_service._get_sensebox_data")
    def test_partial_accessible(self, mock_get_data):
        """Test when some senseBoxes are accessible."""
        # Return data for first call, None for second and third
        mock_get_data.side_effect = [{"sensors": []}, None, None]

        accessible, total = check_sensebox_accessibility()
        self.assertEqual(accessible, 1)
        self.assertEqual(total, 3)


class TestGetCacheAgeSeconds(unittest.TestCase):
    """Test cases for get_cache_age_seconds helper."""

    @patch("src.routes.readyz.valkey_service")
    def test_cache_age_calculation(self, mock_valkey):
        """Test cache age calculation when TTL is available."""
        mock_valkey.ttl.return_value = 10  # 10 seconds remaining

        age = get_cache_age_seconds()
        # CACHE_TTL_SECONDS is 60, so age = 60 - 10 = 50
        self.assertEqual(age, 50)

    @patch("src.routes.readyz.valkey_service")
    def test_cache_age_none_when_no_ttl(self, mock_valkey):
        """Test that None is returned when cache has no TTL."""
        mock_valkey.ttl.return_value = None

        age = get_cache_age_seconds()
        self.assertIsNone(age)

    @patch("src.routes.readyz.valkey_service", None)
    def test_cache_age_none_when_valkey_not_configured(self):
        """Test that None is returned when Valkey is not configured."""
        age = get_cache_age_seconds()
        self.assertIsNone(age)

    @patch("src.routes.readyz.valkey_service")
    def test_cache_age_zero_when_ttl_is_max(self, mock_valkey):
        """Test cache age is 0 when TTL equals CACHE_TTL_SECONDS."""
        mock_valkey.ttl.return_value = 60  # Full TTL remaining

        age = get_cache_age_seconds()
        self.assertEqual(age, 0)


if __name__ == "__main__":
    unittest.main()
