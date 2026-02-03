import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import Mock, patch
from clients.icsclient import ICSClient
from services.config_service import ICS_API_KEY, ICS_URL, ICS_PULLING_INTERVAL


class TestICSClient:
    """Test suite for ICSClient class"""

    @pytest.fixture
    def config(self):
        """Create a test configuration"""
        return {
            'bot': {
                'whitelist': [12345, 67890]
            }
        }

    @pytest.fixture
    def ics_client(self, config):
        """Create an instance of ICSClient"""
        with patch('clients.icsclient.ICS_API_KEY', 'test_api_key'), \
             patch('clients.icsclient.ICS_URL', 'http://test.url'), \
             patch('clients.icsclient.ICS_PULLING_INTERVAL', 5):
            return ICSClient(config)

    def test_init(self, config):
        """Test initialization of ICSClient"""
        with patch('clients.icsclient.ICS_API_KEY', 'test_api_key'), \
             patch('clients.icsclient.ICS_URL', 'http://test.url'), \
             patch('clients.icsclient.ICS_PULLING_INTERVAL', 5):
            client = ICSClient(config)
            
            assert client.config == config
            assert client.api_key == 'test_api_key'
            assert client.base_url == 'http://test.url'
            assert client.whitelist == [12345, 67890]
            assert client.pulling_interval == 300  # 5 minutes in seconds

    @patch('clients.icsclient.requests.get')
    @patch('clients.icsclient.logger')
    def test_fetch_events_success(self, mock_logger, mock_get, ics_client):
        """Test fetch_events method with successful response"""
        # Create mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'events': [
                {'uid': '1', 'title': 'Test Event', 'start_datetime': '2023-01-01T10:00:00'}
            ]
        }
        mock_get.return_value = mock_response
        
        result = ics_client.fetch_events(12345)
        
        # Verify the request was made correctly
        expected_url = f"{ics_client.base_url}?api_key={ics_client.api_key}&user_id=12345"
        mock_get.assert_called_with(expected_url)
        
        # Verify the result
        assert result == [{'uid': '1', 'title': 'Test Event', 'start_datetime': '2023-01-01T10:00:00'}]
        mock_logger.info.assert_called_with("Fetching events for user 12345 from http://test.url?api_key=test_api_key&user_id=12345")

    @patch('clients.icsclient.requests.get')
    @patch('clients.icsclient.logger')
    def test_fetch_events_failure(self, mock_logger, mock_get, ics_client):
        """Test fetch_events method with failed response"""
        # Create mock response with error status
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = ics_client.fetch_events(12345)
        
        # Should return empty list on failure
        assert result == []
        mock_logger.error.assert_called_with("Failed to fetch events for user 12345: 404")

    @patch('clients.icsclient.requests.get')
    @patch('clients.icsclient.logger')
    def test_fetch_events_exception(self, mock_logger, mock_get, ics_client):
        """Test fetch_events method when an exception occurs"""
        # Mock requests.get to raise an exception
        mock_get.side_effect = Exception("Network error")
        
        result = ics_client.fetch_events(12345)
        
        # Should return empty list on exception
        assert result == []
        mock_logger.error.assert_called_with("Error fetching events for user 12345: Network error")

    def test_compare_events_added(self, ics_client):
        """Test compare_events method with added events"""
        old_events = [
            {'uid': '1', 'title': 'Event 1', 'start_datetime': '2023-01-01T10:00:00'}
        ]
        
        new_events = [
            {'uid': '1', 'title': 'Event 1', 'start_datetime': '2023-01-01T10:00:00'},
            {'uid': '2', 'title': 'Event 2', 'start_datetime': '2023-01-02T10:00:00'}
        ]
        
        result = ics_client.compare_events(old_events, new_events)
        
        assert result['added'] == [{'uid': '2', 'title': 'Event 2', 'start_datetime': '2023-01-02T10:00:00'}]
        assert result['removed'] == []
        assert result['modified'] == []

    def test_compare_events_removed(self, ics_client):
        """Test compare_events method with removed events"""
        old_events = [
            {'uid': '1', 'title': 'Event 1', 'start_datetime': '2023-01-01T10:00:00'},
            {'uid': '2', 'title': 'Event 2', 'start_datetime': '2023-01-02T10:00:00'}
        ]
        
        new_events = [
            {'uid': '1', 'title': 'Event 1', 'start_datetime': '2023-01-01T10:00:00'}
        ]
        
        result = ics_client.compare_events(old_events, new_events)
        
        assert result['added'] == []
        assert result['removed'] == [{'uid': '2', 'title': 'Event 2', 'start_datetime': '2023-01-02T10:00:00'}]
        assert result['modified'] == []

    def test_compare_events_modified(self, ics_client):
        """Test compare_events method with modified events"""
        old_events = [
            {'uid': '1', 'title': 'Event 1', 'start_datetime': '2023-01-01T10:00:00'}
        ]
        
        new_events = [
            {'uid': '1', 'title': 'Event 1 Modified', 'start_datetime': '2023-01-01T11:00:00'}
        ]
        
        result = ics_client.compare_events(old_events, new_events)
        
        assert result['added'] == []
        assert result['removed'] == []
        assert len(result['modified']) == 1
        assert result['modified'][0]['old'] == {'uid': '1', 'title': 'Event 1', 'start_datetime': '2023-01-01T10:00:00'}
        assert result['modified'][0]['new'] == {'uid': '1', 'title': 'Event 1 Modified', 'start_datetime': '2023-01-01T11:00:00'}

    def test_compare_events_no_changes(self, ics_client):
        """Test compare_events method with no changes"""
        events = [
            {'uid': '1', 'title': 'Event 1', 'start_datetime': '2023-01-01T10:00:00'}
        ]
        
        result = ics_client.compare_events(events, events)
        
        assert result['added'] == []
        assert result['removed'] == []
        assert result['modified'] == []

    def test_compare_events_empty(self, ics_client):
        """Test compare_events method with empty lists"""
        result = ics_client.compare_events([], [])
        
        assert result['added'] == []
        assert result['removed'] == []
        assert result['modified'] == []