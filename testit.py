#!/usr/bin/env python3

import unittest
import json
import os
import sys
from unittest.mock import patch, MagicMock

# Set up path to find config.py and setup.config
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

from config import get_config_with_defaults
CONFIG = get_config_with_defaults()
SRVC_SHARED_SECRET = CONFIG.get('service', 'SRVC_SHARED_SECRET')

# Import the FastAPI app
from app.main import app
from app.core.config import settings
from app.core.security import get_current_user

class TestFastAPIApp(unittest.TestCase):

    def setUp(self):
        """Set up FastAPI app for testing."""
        from fastapi.testclient import TestClient
        self.client = TestClient(app)

        # Override dependencies to bypass authentication for protected endpoints
        def mock_get_current_user():
            return {"sub": "test-user"}

        app.dependency_overrides[get_current_user] = mock_get_current_user

        # Perform login to obtain JWT token
        self.jwt_token = self.perform_login()

    def tearDown(self):
        """Tear down FastAPI app after testing."""
        app.dependency_overrides.clear()

    def perform_login(self):
        """Perform login to obtain JWT token."""

        # Define login data
        login_data = {
            'api_key': SRVC_SHARED_SECRET
        }

        # Send POST request to /api/v1/login endpoint
        response = self.client.post('/api/v1/login', json=login_data)

        # Extract JWT token from response
        data = response.json()
        jwt_token = data.get('access_token')

        return jwt_token

    def test_health_endpoint(self):
        """Test /api/v1/health endpoint."""
        response = self.client.get('/api/v1/health')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'healthy')

    def test_login_endpoint(self):
        """Test /login endpoint."""

        # Define test data
        test_data = {
            'api_key': SRVC_SHARED_SECRET
        }

        # Send POST request to /api/v1/login endpoint
        response = self.client.post('/api/v1/login', json=test_data)

        # Check if response status code is 200 OK
        self.assertEqual(response.status_code, 200)

        # Check if response contains access token
        data = response.json()
        self.assertIn('access_token', data)

    def test_login_invalid_key(self):
        """Test /login endpoint with invalid key."""
        test_data = {
            'api_key': 'invalid_key'
        }
        response = self.client.post('/api/v1/login', json=test_data)
        self.assertEqual(response.status_code, 401)

    def test_analyze_visit_notes_endpoint(self):
        """Test /api/v1/analyze-visit-notes endpoint."""

        with patch('app.api.v1.endpoints.analyze_visit_notes') as mock_analyze_visit_notes:
            mock_analyze_visit_notes.return_value = True

            # Send GET request to /api/v1/analyze-visit-notes endpoint
            response = self.client.get('/api/v1/analyze-visit-notes')

        # Check if response status code is 200 OK
        self.assertEqual(response.status_code, 200)

        # Check if response contains expected message
        data = response.json()
        self.assertEqual(data['message'], 'analyze_visit_notes completed')

    def test_analyze_visit_note_endpoint(self):
        """Test /api/v1/analyze-visit-note endpoint."""

        with patch('app.api.v1.endpoints.analyze_visit_note') as mock_analyze_visit_note:
            mock_analyze_visit_note.return_value = True

            # Send GET request to /api/v1/analyze-visit-note endpoint with visit_note_id parameter
            response = self.client.get('/api/v1/analyze-visit-note?visit_note_id=1')

        # Check if response status code is 200 OK
        self.assertEqual(response.status_code, 200)

        # Check if response contains expected message
        data = response.json()
        self.assertEqual(data['message'], 'analyze_visit_note completed')

    def test_root_endpoint(self):
        """Test / endpoint."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('message', data)
        self.assertIn('version', data)

if __name__ == '__main__':
    unittest.main()
