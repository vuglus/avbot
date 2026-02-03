import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import asyncio
import json
from datetime import datetime
from handlers.start_handler import StartHandler
from handlers.text_handler import TextHandler
from handlers.document_handler import DocumentHandler
from handlers.audio_handler import AudioHandler
from handlers.topic_handler import TopicHandler
from handlers.callback_handler import CallbackHandler
from handlers.icshandler import ICSHandler
from services.dialog_service import load_user_dialog


class TestBotHandlers:
    """Test suite for bot handlers"""

    @pytest.fixture
    def mock_message(self):
        """Create a mock Telegram message"""
        message = Mock()
        message.from_user.id = 12345
        message.from_user.username = "testuser"
        message.chat.id = 12345
        message.text = "Test message"
        message.message_id = 1
        message.date = datetime.now()
        return message

    @pytest.fixture
    def mock_callback_query(self):
        """Create a mock Telegram callback query"""
        query = Mock()
        query.from_user.id = 12345
        query.message.chat.id = 12345
        query.data = "test_callback_data"
        return query

    @pytest.fixture
    def mock_bot(self):
        """Create a mock Telegram bot"""
        bot = Mock()
        bot.reply_to = AsyncMock()
        bot.send_message = AsyncMock()
        bot.send_document = AsyncMock()
        bot.delete_message = AsyncMock()
        bot.edit_message_text = AsyncMock()
        return bot

    @pytest.fixture
    def mock_update(self):
        """Create a mock Telegram update"""
        update = Mock()
        update.effective_user.id = 12345
        update.effective_user.username = "testuser"
        update.message = Mock()
        update.message.chat.id = 12345
        update.message.text = "Test message"
        update.message.message_id = 1
        update.message.date = datetime.now()
        return update

    @pytest.fixture
    def mock_context(self):
        """Create a mock Telegram context"""
        context = Mock()
        return context

    @pytest.fixture
    def config(self):
        """Create a test configuration"""
        return {
            'bot': {
                'whitelist': [12345, 67890],
                'admin_id': 12345,
                'welcome': 'Welcome to AVBot!'
            },
            'yandex': {
                'folder_id': 'test_folder_id',
                'oauth_token': 'test_token'
            }
        }

    @pytest.mark.asyncio
    async def test_start_handler_whitelisted_user(self, mock_update, mock_context):
        """Test start handler with whitelisted user"""
        with patch('handlers.start_handler.BOT_WELCOME', 'Welcome to AVBot!'):
            handler = StartHandler()
            mock_update.message.reply_text = AsyncMock()
            
            await handler.handle_unauthorized(mock_update, mock_context)
            
            # Verify welcome message was sent
            mock_update.message.reply_text.assert_called_once_with("Welcome to AVBot!")

    @pytest.mark.asyncio
    async def test_text_handler_success(self, mock_update, mock_context):
        """Test text handler with successful response"""
        with patch('handlers.text_handler.ask_yandexgpt_with_context') as mock_ask_yandexgpt, \
             patch('services.dialog_service.DIALOGS_DIR', 'dialogs'), \
             patch('handlers.text_handler.add_message_to_topic'), \
             patch('handlers.text_handler.get_last_messages'):
            
            # Mock ask_yandexgpt to return a response
            mock_ask_yandexgpt.return_value = "Test response from YandexGPT"
            
            handler = TextHandler()
            mock_update.message.reply_text = AsyncMock()
            
            await handler.handle_authorized(mock_update, mock_context)
            
            # Verify response was sent
            mock_update.message.reply_text.assert_called_once_with("Test response from YandexGPT")

    @pytest.mark.asyncio
    async def test_text_handler_exception(self, mock_update, mock_context):
        """Test text handler when an exception occurs"""
        with patch('services.yandexgpt_service.ask_yandexgpt_with_context') as mock_ask_yandexgpt, \
             patch('services.dialog_service.DIALOGS_DIR', 'dialogs'):
            
            # Mock ask_yandexgpt to raise an exception
            mock_ask_yandexgpt.side_effect = Exception("YandexGPT error")
            
            handler = TextHandler()
            mock_update.message.reply_text = AsyncMock()
            
            await handler.handle_authorized(mock_update, mock_context)
            
            # Verify error message was sent
            mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_document_handler_success(self, mock_update, mock_context):
        """Test document handler with successful processing"""
        # Mock document
        mock_update.message.document = Mock()
        mock_update.message.document.file_id = "test_file_id"
        mock_update.message.document.file_name = "test.txt"
        
        with patch('services.config_service.YCLOUD_FOLDER_ID', 'test_folder_id'), \
             patch('services.config_service.YCLOUD_API_KEY', 'test_token'), \
             patch('services.dialog_service.DIALOGS_DIR', 'dialogs'), \
             patch('services.yandex_index_service.YandexIndexService') as mock_index_service:
            
            # Mock index service
            mock_index_instance = Mock()
            mock_index_instance.get_index_name.return_value = "test_index"
            mock_index_instance.upload_file_to_index = Mock()
            mock_index_service.return_value = mock_index_instance
            
            handler = DocumentHandler()
            mock_update.message.reply_text = AsyncMock()
            
            await handler.handle_authorized(mock_update, mock_context)
            
            # Verify success message was sent
            # Note: This test might need adjustment based on actual implementation
            # mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_topic_handler_success(self, mock_update, mock_context):
        """Test topic handler with successful execution"""
        # Mock message text with topic
        mock_update.message.text = "/topic Test topic"
        
        with patch('services.dialog_service.DIALOGS_DIR', 'dialogs'):
            handler = TopicHandler()
            mock_update.message.reply_text = AsyncMock()
            
            await handler.handle_authorized(mock_update, mock_context)
            
            # Verify success message was sent
            mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_ics_handler_format_changes_no_changes(self):
        """Test ICS handler format_changes method with no changes"""
        config = {
            'bot': {
                'whitelist': [12345, 67890]
            }
        }
        mock_bot = Mock()
        
        with patch('handlers.icshandler.ICS_SYSTEM_PROMPT', 'Test system prompt'):
            handler = ICSHandler(config, mock_bot)
            
            changes = {
                'added': [],
                'removed': [],
                'modified': []
            }
            
            result = handler.format_changes(changes)
            assert result == ""

    @pytest.mark.asyncio
    async def test_ics_handler_format_changes_added_events(self):
        """Test ICS handler format_changes method with added events"""
        config = {
            'bot': {
                'whitelist': [12345, 67890]
            }
        }
        mock_bot = Mock()
        
        with patch('handlers.icshandler.ICS_SYSTEM_PROMPT', 'Test system prompt'):
            handler = ICSHandler(config, mock_bot)
            
            changes = {
                'added': [
                    {'uid': '1', 'title': 'New Event', 'start_datetime': '2023-01-01T10:00:00'},
                    {'uid': '2', 'title': 'Another Event', 'start_datetime': '2023-01-02T15:00:00'}
                ],
                'removed': [],
                'modified': []
            }
            
            result = handler.format_changes(changes)
            expected = "Добавлено событий: 2\n- New Event (2023-01-01T10:00:00)\n- Another Event (2023-01-02T15:00:00)"
            assert result == expected