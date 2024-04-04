#!/usr/bin/env python3

import unittest
import json
from unittest.mock import patch, MagicMock

from config import get_config
CONFIG = get_config()
SRVC_SHARED_SECRET=CONFIG.get('service', 'SRVC_SHARED_SECRET')

# Import the Flask app
from zollama import app

class TestFlaskApp(unittest.TestCase):

    def setUp(self):
        """Set up Flask app for testing."""
        app.config['TESTING'] = True
        self.app = app.test_client()

        # Perform login to obtain JWT token
        self.jwt_token = self.perform_login()

    def tearDown(self):
        """Tear down Flask app after testing."""
        pass

    def perform_login(self):
        """Perform login to obtain JWT token."""

        # Define login data
        login_data = {
            'api_key': SRVC_SHARED_SECRET
        }
        headers = {
            'Content-Type' : 'application/json'
            }

        # Send POST request to /login endpoint
        response = self.app.post('/login', json=login_data, headers=headers)

        # Extract JWT token from response
        data = json.loads(response.data)
        jwt_token = data.get('access_token')

        return jwt_token

    def test_login_endpoint(self):
        """Test /login endpoint."""

        # Define test data
        test_data = {
            'api_key': SRVC_SHARED_SECRET 
        }

        headers = {
            'Content-Type' : 'application/json'
            }

        # Send POST request to /login endpoint
        response = self.app.post('/login', json=test_data, headers=headers)

        # Check if response status code is 200 OK
        self.assertEqual(response.status_code, 200)

        # Check if response contains access token
        data = json.loads(response.data)
        self.assertIn('access_token', data)

    @patch('zollama.analyze_visit_notes')
    def test_analyze_visit_notes_endpoint(self, mock_analyze_visit_notes):
        """Test /analyze_visit_notes endpoint."""

        # Mock the analyze_visit_notes function
        mock_analyze_visit_notes.return_value = True

        # Define headers with JWT token
        headers = {
            'Authorization': f'Bearer {self.jwt_token}'
        }

        # Send GET request to /analyze_visit_notes endpoint with headers
        response = self.app.get('/analyze_visit_notes', headers=headers)

        # Check if response status code is 200 OK
        self.assertEqual(response.status_code, 200)

        # Check if response contains expected message
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'analyze_visit_notes endpoint')

    @patch('zollama.analyze_visit_note')
    def test_analyze_visit_note_endpoint(self, mock_analyze_visit_note):
        """Test /analyze_visit_note endpoint."""

        # Mock the analyze_visit_note function
        mock_analyze_visit_note.return_value = True

        # Define headers with JWT token
        headers = {
            'Authorization': f'Bearer {self.jwt_token}'
        }

        # Send GET request to /analyze_visit_note endpoint with visit_note_id parameter
        response = self.app.get('/analyze_visit_note?visit_note_id=1', headers=headers)

        # Check if response status code is 200 OK
        self.assertEqual(response.status_code, 200)

        # Check if response contains expected message
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'analyze_visit_note endpoint')

    # Add more test cases for other endpoints...

if __name__ == '__main__':
    unittest.main()
