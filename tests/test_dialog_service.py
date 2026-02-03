import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import os
import json
import tempfile
from unittest.mock import Mock, patch, mock_open
from services.dialog_service import (
    ensure_dialogs_dir,
    get_user_dialog_file,
    load_user_dialog,
    save_user_dialog,
    add_message_to_topic,
    set_current_topic,
    get_last_messages,
    set_topic_index,
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

    def test_ensure_dialogs_dir_creates_directory(self):
        """Test that ensure_dialogs_dir creates the directory if it doesn't exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = os.path.join(temp_dir, "dialogs_test")
            
            with patch('services.dialog_service.DIALOGS_DIR', test_dir):
                ensure_dialogs_dir()
                assert os.path.exists(test_dir) is True

    def test_ensure_dialogs_dir_existing_directory(self):
        """Test that ensure_dialogs_dir doesn't fail if directory already exists"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = os.path.join(temp_dir, "dialogs_test")
            os.makedirs(test_dir)
            
            with patch('services.dialog_service.DIALOGS_DIR', test_dir):
                ensure_dialogs_dir()  # Should not raise an exception
                assert os.path.exists(test_dir) is True

    def test_get_user_dialog_file(self):
        """Test that get_user_dialog_file returns correct path"""
        user_id = 12345
        expected_path = os.path.join(DIALOGS_DIR, f"{user_id}.json")
        assert get_user_dialog_file(user_id) == expected_path

    def test_load_user_dialog_nonexistent_file(self, temp_dialogs_dir):
        """Test load_user_dialog with nonexistent file"""
        user_id = 99999  # Nonexistent user
        result = load_user_dialog(user_id)
        
        # Should return default structure
        assert isinstance(result, dict)
        assert "current_topic" in result
        assert "topics" in result
        assert DEFAULT_TOPIC in result["topics"]
        assert "messages" in result["topics"][DEFAULT_TOPIC]

    def test_load_user_dialog_existing_file(self, temp_dialogs_dir):
        """Test load_user_dialog with existing file"""
        user_id = 12345
        dialog_data = {
            "current_topic": "test_topic",
            "topics": {
                "test_topic": {
                    "messages": [{"role": "user", "text": "Hello"}]
                }
            }
        }
        
        # Create the dialog file
        dialog_file = os.path.join(temp_dialogs_dir, f"{user_id}.json")
        with open(dialog_file, 'w', encoding='utf-8') as f:
            json.dump(dialog_data, f, ensure_ascii=False, indent=2)
        
        # Load the dialog
        result = load_user_dialog(user_id)
        
        # Check that the data is correct
        assert result["current_topic"] == "test_topic"
        assert "test_topic" in result["topics"]
        assert result["topics"]["test_topic"]["messages"] == [{"role": "user", "text": "Hello"}]
        # Should also have DEFAULT_TOPIC
        assert DEFAULT_TOPIC in result["topics"]

    def test_load_user_dialog_old_format_conversion(self, temp_dialogs_dir):
        """Test load_user_dialog converts old format to new format"""
        user_id = 12345
        # Old format with topics as lists
        old_format = {
            "current_topic": "test_topic",
            "topics": {
                "test_topic": [{"role": "user", "text": "Hello"}],  # Old format: list
                "another_topic": {"messages": [{"role": "user", "text": "World"}]}  # New format: dict
            }
        }
        
        # Create the dialog file with old format
        dialog_file = os.path.join(temp_dialogs_dir, f"{user_id}.json")
        with open(dialog_file, 'w', encoding='utf-8') as f:
            json.dump(old_format, f, ensure_ascii=False, indent=2)
        
        # Load the dialog (should convert to new format)
        result = load_user_dialog(user_id)
        
        # Check that old format was converted
        assert isinstance(result["topics"]["test_topic"], dict)
        assert "messages" in result["topics"]["test_topic"]
        assert result["topics"]["test_topic"]["messages"] == [{"role": "user", "text": "Hello"}]
        
        # Check that new format was preserved
        assert result["topics"]["another_topic"] == {"messages": [{"role": "user", "text": "World"}]}

    def test_load_user_dialog_missing_current_topic(self, temp_dialogs_dir):
        """Test load_user_dialog handles missing current_topic"""
        user_id = 12345
        dialog_data = {
            "topics": {
                "test_topic": {
                    "messages": []
                }
            }
            # current_topic is missing
        }
        
        # Create the dialog file
        dialog_file = os.path.join(temp_dialogs_dir, f"{user_id}.json")
        with open(dialog_file, 'w', encoding='utf-8') as f:
            json.dump(dialog_data, f, ensure_ascii=False, indent=2)
        
        # Load the dialog
        result = load_user_dialog(user_id)
        
        # Should add current_topic as DEFAULT_TOPIC
        assert result["current_topic"] == DEFAULT_TOPIC
        # Should ensure DEFAULT_TOPIC exists in topics
        assert DEFAULT_TOPIC in result["topics"]

    def test_load_user_dialog_missing_default_topic(self, temp_dialogs_dir):
        """Test load_user_dialog ensures default topic exists"""
        user_id = 12345
        dialog_data = {
            "current_topic": "test_topic",
            "topics": {
                "test_topic": {
                    "messages": []
                }
                # DEFAULT_TOPIC is missing
            }
        }
        
        # Create the dialog file
        dialog_file = os.path.join(temp_dialogs_dir, f"{user_id}.json")
        with open(dialog_file, 'w', encoding='utf-8') as f:
            json.dump(dialog_data, f, ensure_ascii=False, indent=2)
        
        # Load the dialog
        result = load_user_dialog(user_id)
        
        # Should ensure DEFAULT_TOPIC exists in topics
        assert DEFAULT_TOPIC in result["topics"]
        assert "messages" in result["topics"][DEFAULT_TOPIC]

    @patch('services.dialog_service.logger')
    def test_load_user_dialog_corrupted_file(self, mock_logger, temp_dialogs_dir):
        """Test load_user_dialog handles corrupted file"""
        user_id = 12345
        # Create a corrupted JSON file
        dialog_file = os.path.join(temp_dialogs_dir, f"{user_id}.json")
        with open(dialog_file, 'w', encoding='utf-8') as f:
            f.write("corrupted json content")
        
        # Load the dialog (should return default structure)
        result = load_user_dialog(user_id)
        
        # Should return default structure
        assert isinstance(result, dict)
        assert "current_topic" in result
        assert "topics" in result
        assert DEFAULT_TOPIC in result["topics"]
        # Should log the error
        mock_logger.error.assert_called()

    def test_save_user_dialog(self, temp_dialogs_dir):
        """Test save_user_dialog saves data correctly"""
        user_id = 12345
        dialog_data = {
            "current_topic": "test_topic",
            "topics": {
                "test_topic": {
                    "messages": [{"role": "user", "text": "Hello"}]
                }
            }
        }
        
        # Save the dialog
        save_user_dialog(user_id, dialog_data)
        
        # Check that file was created
        dialog_file = os.path.join(temp_dialogs_dir, f"{user_id}.json")
        assert os.path.exists(dialog_file) is True
        
        # Load and verify content
        with open(dialog_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert saved_data == dialog_data

    @patch('services.dialog_service.logger')
    def test_save_user_dialog_exception(self, mock_logger, temp_dialogs_dir):
        """Test save_user_dialog handles exceptions"""
        user_id = 12345
        dialog_data = {"current_topic": DEFAULT_TOPIC, "topics": {DEFAULT_TOPIC: {"messages": []}}}
        
        # Mock open to raise an exception
        with patch('builtins.open', mock_open()) as mock_file:
            mock_file.side_effect = Exception("File write error")
            
            save_user_dialog(user_id, dialog_data)
            
            # Should log the error
            mock_logger.error.assert_called()

    def test_add_message_to_topic_new_topic(self, temp_dialogs_dir):
        """Test add_message_to_topic with new topic"""
        user_id = 12345
        message = {"role": "user", "text": "Hello"}
        topic_name = "new_topic"
        
        # Add message to new topic
        add_message_to_topic(user_id, message, topic_name)
        
        # Load and verify the dialog
        result = load_user_dialog(user_id)
        assert topic_name in result["topics"]
        assert result["topics"][topic_name]["messages"] == [message]
        assert result["current_topic"] == DEFAULT_TOPIC  # Should not change current topic

    def test_add_message_to_topic_existing_topic(self, temp_dialogs_dir):
        """Test add_message_to_topic with existing topic"""
        user_id = 12345
        topic_name = "existing_topic"
        initial_message = {"role": "user", "text": "Initial message"}
        
        # Create dialog with existing topic
        dialog_data = {
            "current_topic": DEFAULT_TOPIC,
            "topics": {
                DEFAULT_TOPIC: {"messages": []},
                topic_name: {"messages": [initial_message]}
            }
        }
        save_user_dialog(user_id, dialog_data)
        
        # Add new message to existing topic
        new_message = {"role": "assistant", "text": "Response"}
        add_message_to_topic(user_id, new_message, topic_name)
        
        # Load and verify the dialog
        result = load_user_dialog(user_id)
        assert result["topics"][topic_name]["messages"] == [initial_message, new_message]

    def test_add_message_to_topic_default_topic(self, temp_dialogs_dir):
        """Test add_message_to_topic with default topic when no topic specified"""
        user_id = 12345
        message = {"role": "user", "text": "Hello"}
        
        # Add message without specifying topic (should use current topic)
        add_message_to_topic(user_id, message)
        
        # Load and verify the dialog
        result = load_user_dialog(user_id)
        assert result["topics"][DEFAULT_TOPIC]["messages"] == [message]

    def test_set_current_topic_none(self, temp_dialogs_dir):
        """Test set_current_topic with None (reset to default)"""
        user_id = 12345
        # Set a custom current topic first
        dialog_data = {
            "current_topic": "custom_topic",
            "topics": {
                "custom_topic": {"messages": []},
                DEFAULT_TOPIC: {"messages": []}
            }
        }
        save_user_dialog(user_id, dialog_data)
        
        # Reset to default topic
        result = set_current_topic(user_id, None)
        
        # Load and verify the dialog
        updated_dialog = load_user_dialog(user_id)
        assert updated_dialog["current_topic"] == DEFAULT_TOPIC
        # Should return list of topics
        assert isinstance(result, list)

    def test_set_current_topic_specific(self, temp_dialogs_dir):
        """Test set_current_topic with specific topic"""
        user_id = 12345
        topic_name = "test_topic"
        
        # Set specific topic
        result = set_current_topic(user_id, topic_name)
        
        # Load and verify the dialog
        updated_dialog = load_user_dialog(user_id)
        assert updated_dialog["current_topic"] == topic_name
        # Should create topic if it doesn't exist
        assert topic_name in updated_dialog["topics"]
        # Should return confirmation message
        assert f"Текущая тема установлена: {topic_name}" == result

    def test_set_current_topic_existing(self, temp_dialogs_dir):
        """Test set_current_topic with existing topic"""
        user_id = 12345
        topic_name = "existing_topic"
        
        # Create dialog with existing topic
        dialog_data = {
            "current_topic": DEFAULT_TOPIC,
            "topics": {
                DEFAULT_TOPIC: {"messages": []},
                topic_name: {"messages": [{"role": "user", "text": "Hello"}]}
            }
        }
        save_user_dialog(user_id, dialog_data)
        
        # Set to existing topic
        result = set_current_topic(user_id, topic_name)
        
        # Load and verify the dialog
        updated_dialog = load_user_dialog(user_id)
        assert updated_dialog["current_topic"] == topic_name
        # Should not modify existing topic content
        assert updated_dialog["topics"][topic_name]["messages"] == [{"role": "user", "text": "Hello"}]

    def test_get_last_messages_default(self, temp_dialogs_dir):
        """Test get_last_messages with default topic"""
        user_id = 12345
        messages = [
            {"role": "user", "text": "Message 1"},
            {"role": "assistant", "text": "Message 2"},
            {"role": "user", "text": "Message 3"}
        ]
        
        # Create dialog with messages
        dialog_data = {
            "current_topic": DEFAULT_TOPIC,
            "topics": {
                DEFAULT_TOPIC: {"messages": messages}
            }
        }
        save_user_dialog(user_id, dialog_data)
        
        # Get last messages
        result = get_last_messages(user_id, count=2)
        
        # Should return last 2 messages
        assert result == messages[-2:]

    def test_get_last_messages_specific_topic(self, temp_dialogs_dir):
        """Test get_last_messages with specific topic"""
        user_id = 12345
        topic_name = "test_topic"
        messages = [
            {"role": "user", "text": "Topic message 1"},
            {"role": "assistant", "text": "Topic message 2"}
        ]
        
        # Create dialog with messages in specific topic
        dialog_data = {
            "current_topic": DEFAULT_TOPIC,
            "topics": {
                DEFAULT_TOPIC: {"messages": []},
                topic_name: {"messages": messages}
            }
        }
        save_user_dialog(user_id, dialog_data)
        
        # Get messages from specific topic
        result = get_last_messages(user_id, count=10, topic_name=topic_name)
        
        # Should return all messages from specified topic
        assert result == messages

    def test_get_last_messages_nonexistent_topic(self, temp_dialogs_dir):
        """Test get_last_messages with nonexistent topic"""
        user_id = 12345
        nonexistent_topic = "nonexistent_topic"
        
        # Create dialog without the topic
        dialog_data = {
            "current_topic": DEFAULT_TOPIC,
            "topics": {
                DEFAULT_TOPIC: {"messages": []}
            }
        }
        save_user_dialog(user_id, dialog_data)
        
        # Get messages from nonexistent topic
        result = get_last_messages(user_id, count=10, topic_name=nonexistent_topic)
        
        # Should return empty list from default topic
        assert result == []

    def test_get_last_messages_exceeding_count(self, temp_dialogs_dir):
        """Test get_last_messages when requesting more messages than available"""
        user_id = 12345
        messages = [
            {"role": "user", "text": "Message 1"},
            {"role": "assistant", "text": "Message 2"}
        ]
        
        # Create dialog with fewer messages than requested count
        dialog_data = {
            "current_topic": DEFAULT_TOPIC,
            "topics": {
                DEFAULT_TOPIC: {"messages": messages}
            }
        }
        save_user_dialog(user_id, dialog_data)
        
        # Request more messages than available
        result = get_last_messages(user_id, count=10)
        
        # Should return all available messages
        assert result == messages

    def test_set_topic_index_new_topic(self, temp_dialogs_dir):
        """Test set_topic_index with new topic"""
        user_id = 12345
        topic_name = "new_topic"
        index_id = "test_index_id"
        
        # Set index for new topic
        set_topic_index(user_id, topic_name, index_id)
        
        # Load and verify the dialog
        result = load_user_dialog(user_id)
        assert topic_name in result["topics"]
        assert "index_id" in result["topics"][topic_name]
        assert result["topics"][topic_name]["index_id"] == index_id
        # Should also have messages array
        assert "messages" in result["topics"][topic_name]

    def test_set_topic_index_existing_topic(self, temp_dialogs_dir):
        """Test set_topic_index with existing topic"""
        user_id = 12345
        topic_name = "existing_topic"
        index_id = "test_index_id"
        
        # Create dialog with existing topic
        dialog_data = {
            "current_topic": DEFAULT_TOPIC,
            "topics": {
                DEFAULT_TOPIC: {"messages": []},
                topic_name: {"messages": [{"role": "user", "text": "Hello"}]}
            }
        }
        save_user_dialog(user_id, dialog_data)
        
        # Set index for existing topic
        set_topic_index(user_id, topic_name, index_id)
        
        # Load and verify the dialog
        result = load_user_dialog(user_id)
        assert result["topics"][topic_name]["index_id"] == index_id
        # Should preserve existing messages
        assert result["topics"][topic_name]["messages"] == [{"role": "user", "text": "Hello"}]