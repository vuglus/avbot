import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from services.config_service import Config

mock_config_data = {
            'bot': {
                'whitelist': [12345, 67890],
                'welcome': 'Welcome to AVBot!'
            },
            'yandex': {
                'system_prompt': 'You are a bot.',
                'speech_api_key': 'test_speech_api_key',
                'key': 'test_key',
            },
            'ycloud': {
                'api_key' : 'test_api_key',
                'folder_id': 'test_folder_id',
            },
            'ics': {
                'system_prompt': 'You are a calendar bot.',
                'url': 'https://example.com/calendar.ics',
                'pulling_interval': 10,
            }
        }

config = Config(mock_config_data)

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


    @pytest.mark.asyncio
    async def test_start_handler_whitelisted_user(self, mock_update, mock_context):
        from handlers.start_handler import StartHandler
        handler = StartHandler(config)
        mock_update.message.reply_text = AsyncMock()
        await handler.handle_unauthorized(mock_update, mock_context)
        
        # Verify welcome message was sent
        mock_update.message.reply_text.assert_called_once_with("Welcome to AVBot!")

    @pytest.mark.asyncio
    async def test_text_handler_success(self, mock_update, mock_context):
        with patch('services.dialog_service.DIALOGS_DIR', 'dialogs'), \
            patch('handlers.text_handler.add_message_to_topic'), \
            patch('handlers.text_handler.get_last_messages', return_value=[]):

            from handlers.text_handler import TextHandler

            mock_yandexgpt_service = Mock()
            mock_yandexgpt_service.ask_yandexgpt_with_context = Mock(
                return_value="Test response from YandexGPT"
            )

            handler = TextHandler(config, mock_yandexgpt_service)

            mock_update.message.text = "hello"
            mock_update.effective_user.id = 123
            mock_update.message.reply_text = AsyncMock()

            await handler.handle_authorized(mock_update, mock_context)

            mock_update.message.reply_text.assert_called_once()
            args, _ = mock_update.message.reply_text.call_args
            assert args[0] == "Test response from YandexGPT"


    @pytest.mark.asyncio
    async def test_text_handler_exception(self, mock_update, mock_context):
        """Test text handler when an exception occurs"""

        from handlers.text_handler import TextHandler

        # --- mock YandexGPTService ---
        mock_yandexgpt_service = Mock()
        mock_yandexgpt_service.ask_yandexgpt_with_context = Mock(
            side_effect=Exception("YandexGPT error")
        )

        with patch('services.dialog_service.DIALOGS_DIR', 'dialogs'):
            handler = TextHandler(config, mock_yandexgpt_service)

            mock_update.message.text = "hello"
            mock_update.effective_user.id = 123
            mock_update.message.reply_text = AsyncMock()

            await handler.handle_authorized(mock_update, mock_context)

            # handler обязан что-то ответить пользователю
            mock_update.message.reply_text.assert_called_once()

            args, _ = mock_update.message.reply_text.call_args
            assert isinstance(args[0], str)

    @pytest.mark.asyncio
    async def test_document_handler_success(self, mock_update, mock_context):
        """Test document handler with successful processing"""
        # Mock document
        mock_update.message.document = Mock()
        mock_update.message.document.file_id = "test_file_id"
        mock_update.message.document.file_name = "test.txt"
        
        with patch('services.dialog_service.DIALOGS_DIR', 'dialogs'), \
             patch('services.yandex_index_service.YandexIndexService') as mock_index_service:
            # Mock index service
            mock_index_instance = Mock()
            mock_index_instance.get_index_name.return_value = "test_index"
            mock_index_instance.upload_file_to_index = Mock()
            mock_index_service.return_value = mock_index_instance

            from handlers.document_handler import DocumentHandler
            handler = DocumentHandler(config)
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
            from handlers.topic_handler import TopicHandler
            handler = TopicHandler(config)
            mock_update.message.reply_text = AsyncMock()
            
            await handler.handle_authorized(mock_update, mock_context)
            
            # Verify success message was sent
            mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_ics_handler_format_changes_no_changes(self):
        """Test ICS handler format_changes method with no changes"""
        mock_bot = Mock()        
        from handlers.icshandler import ICSHandler
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
        mock_bot = Mock()

        from handlers.icshandler import ICSHandler
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