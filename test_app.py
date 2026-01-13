import unittest
import json
from app import app, VERSION


class TestVersionEndpoint(unittest.TestCase):
    """Test cases for the /version endpoint."""
    
    def setUp(self):
        """Set up test client."""
        self.app = app
        self.client = self.app.test_client()
        self.app.testing = True
    
    def test_version_endpoint_exists(self):
        """Test that /version endpoint exists and returns 200."""
        response = self.client.get('/version')
        self.assertEqual(response.status_code, 200)
    
    def test_version_endpoint_returns_json(self):
        """Test that /version endpoint returns JSON."""
        response = self.client.get('/version')
        self.assertEqual(response.content_type, 'application/json')
    
    def test_version_endpoint_returns_correct_version(self):
        """Test that /version endpoint returns the correct version."""
        response = self.client.get('/version')
        data = json.loads(response.data)
        self.assertIn('version', data)
        self.assertEqual(data['version'], VERSION)
    
    def test_version_endpoint_no_parameters(self):
        """Test that /version endpoint works without parameters."""
        response = self.client.get('/version')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('version', data)


if __name__ == '__main__':
    unittest.main()
