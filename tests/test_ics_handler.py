import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio
from handlers.icshandler import ICSHandler
from services.config_service import ICS_SYSTEM_PROMPT


class TestICSHandler:
    """Test suite for ICSHandler class"""

    @pytest.fixture
    def config(self):
        """Create a test configuration"""
        return {
            'bot': {
                'whitelist': [12345, 67890]
            }
        }

    @pytest.fixture
    def mock_bot(self):
        """Create a mock Telegram bot"""
        return Mock()

    @pytest.fixture
    def ics_handler(self, config, mock_bot):
        """Create an instance of ICSHandler"""
        with patch('handlers.icshandler.ICS_SYSTEM_PROMPT', 'Test system prompt'):
            return ICSHandler(config, mock_bot)

    def test_init(self, config, mock_bot):
        """Test initialization of ICSHandler"""
        with patch('handlers.icshandler.ICS_SYSTEM_PROMPT', 'Test system prompt'):
            handler = ICSHandler(config, mock_bot)
            
            assert handler.config == config
            assert handler.bot == mock_bot
            assert handler.system_prompt == 'Test system prompt'
            assert handler.whitelist == [12345, 67890]
            assert handler.user_states == {}

    def test_format_changes_no_changes(self, ics_handler):
        """Test format_changes method with no changes"""
        changes = {
            'added': [],
            'removed': [],
            'modified': []
        }
        
        result = ics_handler.format_changes(changes)
        assert result == ""

    def test_format_changes_added_events(self, ics_handler):
        """Test format_changes method with added events"""
        changes = {
            'added': [
                {'uid': '1', 'title': 'New Event', 'start_datetime': '2023-01-01T10:00:00'},
                {'uid': '2', 'title': 'Another Event', 'start_datetime': '2023-01-02T15:00:00'}
            ],
            'removed': [],
            'modified': []
        }
        
        result = ics_handler.format_changes(changes)
        expected = "Добавлено событий: 2\n- New Event (2023-01-01T10:00:00)\n- Another Event (2023-01-02T15:00:00)"
        assert result == expected

    def test_format_changes_removed_events(self, ics_handler):
        """Test format_changes method with removed events"""
        changes = {
            'added': [],
            'removed': [
                {'uid': '1', 'title': 'Cancelled Event', 'start_datetime': '2023-01-01T10:00:00'}
            ],
            'modified': []
        }
        
        result = ics_handler.format_changes(changes)
        expected = "Удалено событий: 1\n- Cancelled Event (2023-01-01T10:00:00)"
        assert result == expected

    def test_format_changes_modified_events(self, ics_handler):
        """Test format_changes method with modified events"""
        changes = {
            'added': [],
            'removed': [],
            'modified': [
                {
                    'old': {'uid': '1', 'title': 'Old Event', 'start_datetime': '2023-01-01T10:00:00'},
                    'new': {'uid': '1', 'title': 'Updated Event', 'start_datetime': '2023-01-01T11:00:00'}
                }
            ]
        }
        
        result = ics_handler.format_changes(changes)
        expected = "Изменено событий: 1\n- Updated Event (2023-01-01T11:00:00)"
        assert result == expected

    def test_format_changes_mixed_changes(self, ics_handler):
        """Test format_changes method with mixed changes"""
        changes = {
            'added': [
                {'uid': '1', 'title': 'New Event', 'start_datetime': '2023-01-01T10:00:00'}
            ],
            'removed': [
                {'uid': '2', 'title': 'Removed Event', 'start_datetime': '2023-01-02T10:00:00'}
            ],
            'modified': [
                {
                    'old': {'uid': '3', 'title': 'Old Event', 'start_datetime': '2023-01-03T10:00:00'},
                    'new': {'uid': '3', 'title': 'Updated Event', 'start_datetime': '2023-01-03T11:00:00'}
                }
            ]
        }
        
        result = ics_handler.format_changes(changes)
        assert "Добавлено событий: 1" in result
        assert "Удалено событий: 1" in result
        assert "Изменено событий: 1" in result
        assert "- New Event (2023-01-01T10:00:00)" in result
        assert "- Removed Event (2023-01-02T10:00:00)" in result
        assert "- Updated Event (2023-01-03T11:00:00)" in result

    @patch('handlers.icshandler.ask_yandexgpt')
    @pytest.mark.asyncio
    async def test_send_notification_with_changes(self, mock_ask_yandexgpt, ics_handler):
        """Test send_notification method with changes"""
        # Mock the ask_yandexgpt function
        mock_ask_yandexgpt.return_value = "Test response from YandexGPT"
        
        # Mock the bot's send_message method
        ics_handler.bot.send_message = AsyncMock()
        
        changes = {
            'added': [
                {'uid': '1', 'title': 'New Event', 'start_datetime': '2023-01-01T10:00:00'}
            ],
            'removed': [],
            'modified': []
        }
        
        await ics_handler.send_notification(12345, changes)
        
        # Verify ask_yandexgpt was called with correct prompt
        expected_prompt = "Test system prompt\n\nДобавлено событий: 1\n- New Event (2023-01-01T10:00:00)"
        mock_ask_yandexgpt.assert_called_with(expected_prompt, 12345)
        
        # Verify bot.send_message was called
        ics_handler.bot.send_message.assert_called_with(
            chat_id=12345,
            text="Обновления в календаре:\n\nTest response from YandexGPT"
        )

    @pytest.mark.asyncio
    async def test_send_notification_no_changes(self, ics_handler):
        """Test send_notification method with no changes"""
        # Mock the bot's send_message method
        ics_handler.bot.send_message = AsyncMock()
        
        changes = {
            'added': [],
            'removed': [],
            'modified': []
        }
        
        await ics_handler.send_notification(12345, changes)
        
        # Should not send any message when there are no changes
        ics_handler.bot.send_message.assert_not_called()

    @patch('handlers.icshandler.ask_yandexgpt')
    @patch('handlers.icshandler.logger')
    @pytest.mark.asyncio
    async def test_send_notification_exception(self, mock_logger, mock_ask_yandexgpt, ics_handler):
        """Test send_notification method when an exception occurs"""
        # Mock ask_yandexgpt to raise an exception
        mock_ask_yandexgpt.side_effect = Exception("YandexGPT error")
        
        changes = {
            'added': [
                {'uid': '1', 'title': 'New Event', 'start_datetime': '2023-01-01T10:00:00'}
            ],
            'removed': [],
            'modified': []
        }
        
        await ics_handler.send_notification(12345, changes)
        
        # Should log the error
        mock_logger.error.assert_called_with("Failed to send notification to user 12345: YandexGPT error")

    def test_check_user_events_with_changes(self, ics_handler):
        """Test check_user_events method with changes"""
        # Mock the ICSClient and its compare_events method
        with patch('clients.icsclient.ICSClient') as mock_ics_client_class:
            mock_ics_client = Mock()
            mock_ics_client_class.return_value = mock_ics_client
            
            # Mock compare_events to return changes
            mock_ics_client.compare_events.return_value = {
                'added': [{'uid': '1', 'title': 'New Event', 'start_datetime': '2023-01-01T10:00:00'}],
                'removed': [],
                'modified': []
            }
            
            # Set up initial state
            ics_handler.user_states[12345] = []
            
            # Mock asyncio.create_task
            with patch('asyncio.create_task') as mock_create_task:
                ics_handler.check_user_events(12345, [{'uid': '1', 'title': 'New Event', 'start_datetime': '2023-01-01T10:00:00'}])
                
                # Verify compare_events was called
                mock_ics_client.compare_events.assert_called()
                
                # Verify asyncio.create_task was called to schedule notification
                mock_create_task.assert_called_once()
                
                # Verify user state was updated
                assert 12345 in ics_handler.user_states

    def test_check_user_events_no_changes(self, ics_handler):
        """Test check_user_events method with no changes"""
        # Mock the ICSClient and its compare_events method
        with patch('clients.icsclient.ICSClient') as mock_ics_client_class:
            mock_ics_client = Mock()
            mock_ics_client_class.return_value = mock_ics_client
            
            # Mock compare_events to return no changes
            mock_ics_client.compare_events.return_value = {
                'added': [],
                'removed': [],
                'modified': []
            }
            
            # Set up initial state
            ics_handler.user_states[12345] = [{'uid': '1', 'title': 'Event', 'start_datetime': '2023-01-01T10:00:00'}]
            
            # Mock asyncio.create_task
            with patch('asyncio.create_task') as mock_create_task:
                ics_handler.check_user_events(12345, [{'uid': '1', 'title': 'Event', 'start_datetime': '2023-01-01T10:00:00'}])
                
                # Verify compare_events was called
                mock_ics_client.compare_events.assert_called()
                
                # Should not schedule notification when there are no changes
                mock_create_task.assert_not_called()
                
                # User state should remain unchanged
                assert ics_handler.user_states[12345] == [{'uid': '1', 'title': 'Event', 'start_datetime': '2023-01-01T10:00:00'}]

    @patch('handlers.icshandler.logger')
    def test_check_user_events_exception(self, mock_logger, ics_handler):
        """Test check_user_events method when an exception occurs"""
        # Mock the ICSClient to raise an exception
        with patch('clients.icsclient.ICSClient') as mock_ics_client_class:
            mock_ics_client_class.side_effect = Exception("ICS client error")
            
            ics_handler.check_user_events(12345, [])
            
            # Should log the error
            mock_logger.error.assert_called_with("Error checking events for user 12345: ICS client error")

    @pytest.mark.asyncio
    async def test_monitor_loop(self, ics_handler):
        """Test monitor_loop method"""
        # Mock the ICSClient
        mock_ics_client = Mock()
        mock_ics_client.pulling_interval = 0.1  # Short interval for testing
        mock_ics_client.fetch_events.return_value = []
        
        # Mock the check_user_events method
        ics_handler.check_user_events = Mock()
        
        # Create a task for the monitor loop and cancel it after a short time
        task = asyncio.create_task(ics_handler.monitor_loop(mock_ics_client))
        
        # Wait briefly to allow the loop to run
        await asyncio.sleep(0.2)
        
        # Cancel the task
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Verify the methods were called
        mock_ics_client.fetch_events.assert_called()
        ics_handler.check_user_events.assert_called()

    @pytest.mark.asyncio
    async def test_monitor_loop_exception(self, ics_handler):
        """Test monitor_loop method when an exception occurs"""
        # Mock the ICSClient to raise an exception
        mock_ics_client = Mock()
        mock_ics_client.pulling_interval = 0.1
        mock_ics_client.fetch_events.side_effect = Exception("Fetch error")
        
        # Mock logger
        with patch('handlers.icshandler.logger') as mock_logger:
            # Create a task for the monitor loop and cancel it after a short time
            task = asyncio.create_task(ics_handler.monitor_loop(mock_ics_client))
            
            # Wait briefly to allow the loop to run
            await asyncio.sleep(0.2)
            
            # Cancel the task
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            # Should log the error
            mock_logger.error.assert_called()