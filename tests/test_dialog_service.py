import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import os
import json
import tempfile
from unittest.mock import Mock, patch, mock_open
from services.dialog_service import (
    DialogService,
    FileDialogStorage,
    DIALOGS_DIR,
    DEFAULT_TOPIC
)


class TestDialogService:
    """Test suite for dialog service functions"""

    @pytest.fixture
    def temp_dialogs_dir(self):
        """Create a temporary dialogs directory for testing"""
        original_dir = DIALOGS_DIR
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change DIALOGS_DIR to point to our temp directory
            with patch('services.dialog_service.DIALOGS_DIR', temp_dir):
                yield temp_dir

    @pytest.fixture
    def dialog_service(self, temp_dialogs_dir):
        """Create a DialogService instance with FileDialogStorage"""
        storage = FileDialogStorage(temp_dialogs_dir)
        return DialogService(storage)

    def test_add_message_to_topic_new_topic(self, dialog_service, temp_dialogs_dir):
        """Test add_message_to_topic with new topic"""
        user_id = 12345
        message = {"role": "user", "text": "Hello"}
        topic_name = "new_topic"
        
        # Add message to new topic
        dialog_service.add_message_to_topic(user_id, message, topic_name)
        
        # Load and verify the dialog
        storage = FileDialogStorage(temp_dialogs_dir)
        result = storage.load_dialog(user_id)
        assert topic_name in result["topics"]
        assert result["topics"][topic_name]["messages"] == [message]
        assert result["current_topic"] == DEFAULT_TOPIC  # Should not change current topic

    def test_add_message_to_topic_existing_topic(self, dialog_service, temp_dialogs_dir):
        """Test add_message_to_topic with existing topic"""
        user_id = 12345
        topic_name = "existing_topic"
        initial_message = {"role": "user", "text": "Initial message"}
        
        # Create dialog with existing topic
        storage = FileDialogStorage(temp_dialogs_dir)
        dialog_data = {
            "current_topic": DEFAULT_TOPIC,
            "topics": {
                DEFAULT_TOPIC: {"messages": []},
                topic_name: {"messages": [initial_message]}
            }
        }
        storage.save_dialog(user_id, dialog_data)
        
        # Add new message to existing topic
        new_message = {"role": "assistant", "text": "Response"}
        dialog_service.add_message_to_topic(user_id, new_message, topic_name)
        
        # Load and verify the dialog
        result = storage.load_dialog(user_id)
        assert result["topics"][topic_name]["messages"] == [initial_message, new_message]

    def test_add_message_to_topic_default_topic(self, dialog_service, temp_dialogs_dir):
        """Test add_message_to_topic with default topic when no topic specified"""
        user_id = 12345
        message = {"role": "user", "text": "Hello"}
        
        # Add message without specifying topic (should use current topic)
        dialog_service.add_message_to_topic(user_id, message)
        
        # Load and verify the dialog
        storage = FileDialogStorage(temp_dialogs_dir)
        result = storage.load_dialog(user_id)
        assert result["topics"][DEFAULT_TOPIC]["messages"] == [message]

    def test_set_current_topic_none(self, dialog_service, temp_dialogs_dir):
        """Test set_current_topic with None (reset to default)"""
        user_id = 12345
        # Set a custom current topic first
        storage = FileDialogStorage(temp_dialogs_dir)
        dialog_data = {
            "current_topic": "custom_topic",
            "topics": {
                "custom_topic": {"messages": []},
                DEFAULT_TOPIC: {"messages": []}
            }
        }
        storage.save_dialog(user_id, dialog_data)
        
        # Reset to default topic
        result = dialog_service.set_current_topic(user_id, None)
        
        # Load and verify the dialog
        updated_dialog = storage.load_dialog(user_id)
        assert updated_dialog["current_topic"] == DEFAULT_TOPIC
        # Should return list of topics
        assert isinstance(result, list)

    def test_set_current_topic_specific(self, dialog_service, temp_dialogs_dir):
        """Test set_current_topic with specific topic"""
        user_id = 12345
        topic_name = "test_topic"
        
        # Set specific topic
        result = dialog_service.set_current_topic(user_id, topic_name)
        
        # Load and verify the dialog
        storage = FileDialogStorage(temp_dialogs_dir)
        updated_dialog = storage.load_dialog(user_id)
        assert updated_dialog["current_topic"] == topic_name
        # Should create topic if it doesn't exist
        assert topic_name in updated_dialog["topics"]
        # Should return confirmation message
        assert f"Текущая тема установлена: {topic_name}" == result

    def test_set_current_topic_existing(self, dialog_service, temp_dialogs_dir):
        """Test set_current_topic with existing topic"""
        user_id = 12345
        topic_name = "existing_topic"
        
        # Create dialog with existing topic
        storage = FileDialogStorage(temp_dialogs_dir)
        dialog_data = {
            "current_topic": DEFAULT_TOPIC,
            "topics": {
                DEFAULT_TOPIC: {"messages": []},
                topic_name: {"messages": [{"role": "user", "text": "Hello"}]}
            }
        }
        storage.save_dialog(user_id, dialog_data)
        
        # Set to existing topic
        result = dialog_service.set_current_topic(user_id, topic_name)
        
        # Load and verify the dialog
        updated_dialog = storage.load_dialog(user_id)
        assert updated_dialog["current_topic"] == topic_name
        # Should not modify existing topic content
        assert updated_dialog["topics"][topic_name]["messages"] == [{"role": "user", "text": "Hello"}]

    def test_get_last_messages_default(self, dialog_service, temp_dialogs_dir):
        """Test get_last_messages with default topic"""
        user_id = 12345
        messages = [
            {"role": "user", "text": "Message 1"},
            {"role": "assistant", "text": "Message 2"},
            {"role": "user", "text": "Message 3"}
        ]
        
        # Create dialog with messages
        storage = FileDialogStorage(temp_dialogs_dir)
        dialog_data = {
            "current_topic": DEFAULT_TOPIC,
            "topics": {
                DEFAULT_TOPIC: {"messages": messages}
            }
        }
        storage.save_dialog(user_id, dialog_data)
        
        # Get last messages
        result = dialog_service.get_last_messages(user_id, count=2)
        
        # Should return last 2 messages
        assert result == messages[-2:]

    def test_get_last_messages_specific_topic(self, dialog_service, temp_dialogs_dir):
        """Test get_last_messages with specific topic"""
        user_id = 12345
        topic_name = "test_topic"
        messages = [
            {"role": "user", "text": "Topic message 1"},
            {"role": "assistant", "text": "Topic message 2"}
        ]
        
        # Create dialog with messages in specific topic
        storage = FileDialogStorage(temp_dialogs_dir)
        dialog_data = {
            "current_topic": DEFAULT_TOPIC,
            "topics": {
                DEFAULT_TOPIC: {"messages": []},
                topic_name: {"messages": messages}
            }
        }
        storage.save_dialog(user_id, dialog_data)
        
        # Get messages from specific topic
        result = dialog_service.get_last_messages(user_id, count=10, topic_name=topic_name)
        
        # Should return all messages from specified topic
        assert result == messages

    def test_get_last_messages_nonexistent_topic(self, dialog_service, temp_dialogs_dir):
        """Test get_last_messages with nonexistent topic"""
        user_id = 12345
        nonexistent_topic = "nonexistent_topic"
        
        # Create dialog without the topic
        storage = FileDialogStorage(temp_dialogs_dir)
        dialog_data = {
            "current_topic": DEFAULT_TOPIC,
            "topics": {
                DEFAULT_TOPIC: {"messages": []}
            }
        }
        storage.save_dialog(user_id, dialog_data)
        
        # Get messages from nonexistent topic
        result = dialog_service.get_last_messages(user_id, count=10, topic_name=nonexistent_topic)
        
        # Should return empty list from default topic
        assert result == []

    def test_get_last_messages_exceeding_count(self, dialog_service, temp_dialogs_dir):
        """Test get_last_messages when requesting more messages than available"""
        user_id = 12345
        messages = [
            {"role": "user", "text": "Message 1"},
            {"role": "assistant", "text": "Message 2"}
        ]
        
        # Create dialog with fewer messages than requested count
        storage = FileDialogStorage(temp_dialogs_dir)
        dialog_data = {
            "current_topic": DEFAULT_TOPIC,
            "topics": {
                DEFAULT_TOPIC: {"messages": messages}
            }
        }
        storage.save_dialog(user_id, dialog_data)
        
        # Request more messages than available
        result = dialog_service.get_last_messages(user_id, count=10)
        
        # Should return all available messages
        assert result == messages

    def test_set_topic_index_new_topic(self, dialog_service, temp_dialogs_dir):
        """Test set_topic_index with new topic"""
        user_id = 12345
        topic_name = "new_topic"
        index_id = "test_index_id"
        
        # Set index for new topic
        dialog_service.set_topic_index(user_id, topic_name, index_id)
        
        # Load and verify the dialog
        storage = FileDialogStorage(temp_dialogs_dir)
        result = storage.load_dialog(user_id)
        assert topic_name in result["topics"]
        assert "index_id" in result["topics"][topic_name]
        assert result["topics"][topic_name]["index_id"] == index_id
        # Should also have messages array
        assert "messages" in result["topics"][topic_name]

    def test_set_topic_index_existing_topic(self, dialog_service, temp_dialogs_dir):
        """Test set_topic_index with existing topic"""
        user_id = 12345
        topic_name = "existing_topic"
        index_id = "test_index_id"
        
        # Create dialog with existing topic
        storage = FileDialogStorage(temp_dialogs_dir)
        dialog_data = {
            "current_topic": DEFAULT_TOPIC,
            "topics": {
                DEFAULT_TOPIC: {"messages": []},
                topic_name: {"messages": [{"role": "user", "text": "Hello"}]}
            }
        }
        storage.save_dialog(user_id, dialog_data)
        
        # Set index for existing topic
        dialog_service.set_topic_index(user_id, topic_name, index_id)
        
        # Load and verify the dialog
        result = storage.load_dialog(user_id)
        assert result["topics"][topic_name]["index_id"] == index_id
        # Should preserve existing messages
        assert result["topics"][topic_name]["messages"] == [{"role": "user", "text": "Hello"}]