import unittest

from src.services.temperature_service import (
    TemperatureResponse,
    _deserialize_temperature_response,
    _serialize_temperature_response,
)


class TestTemperatureServiceSerialization(unittest.TestCase):
    """Unit tests for temperature response serialization."""

    def test_serialize_temperature_response(self):
        response = TemperatureResponse(
            average_temperature=22.5,
            status="Good",
            data_age_seconds=None,
        )
        payload = _serialize_temperature_response(response)

        self.assertEqual(
            payload,
            {"average_temperature": 22.5, "status": "Good", "data_age_seconds": None},
        )

    def test_deserialize_temperature_response(self):
        payload = {
            "average_temperature": "20.0",
            "status": "Good",
            "data_age_seconds": None,
        }
        response = _deserialize_temperature_response(payload)

        self.assertIsNotNone(response)
        self.assertEqual(response.average_temperature, 20.0)
        self.assertEqual(response.status, "Good")
        self.assertEqual(response.data_age_seconds, None)

    def test_deserialize_temperature_response_invalid_payload(self):
        payload = {"status": "Good"}

        self.assertIsNone(_deserialize_temperature_response(payload))


if __name__ == "__main__":
    unittest.main()
