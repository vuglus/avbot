import os
import json
import logging
from typing import List, Dict
from datetime import datetime

DIALOGS_DIR = "dialogs"
DEFAULT_TOPIC = "default"

logger = logging.getLogger(__name__)

def ensure_dialogs_dir():
    """Ensure the dialogs directory exists"""
    if not os.path.exists(DIALOGS_DIR):
        os.makedirs(DIALOGS_DIR)

def get_user_dialog_file(user_id: int) -> str:
    """Get the file path for a user's dialog"""
    return os.path.join(DIALOGS_DIR, f"{user_id}.json")

def load_user_dialog(user_id: int) -> Dict:
    """Load a user's dialog data from file"""
    dialog_file = get_user_dialog_file(user_id)
    
    if not os.path.exists(dialog_file):
        # Return default structure if file doesn't exist
        return {
            "current_topic": DEFAULT_TOPIC,
            "topics": {
                DEFAULT_TOPIC: []
            }
        }
    
    try:
        with open(dialog_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading dialog for user {user_id}: {str(e)}")
        # Return default structure if there's an error
        return {
            "current_topic": DEFAULT_TOPIC,
            "topics": {
                DEFAULT_TOPIC: []
            }
        }

def save_user_dialog(user_id: int, dialog_data: Dict):
    """Save a user's dialog data to file"""
    ensure_dialogs_dir()
    dialog_file = get_user_dialog_file(user_id)
    
    try:
        with open(dialog_file, 'w', encoding='utf-8') as f:
            json.dump(dialog_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving dialog for user {user_id}: {str(e)}")

def add_message_to_topic(user_id: int, message: Dict):
    """Add a message to the current topic for a user"""
    dialog = load_user_dialog(user_id)
    current_topic = dialog.get("current_topic", DEFAULT_TOPIC)
    
    # Ensure topic exists
    if current_topic not in dialog["topics"]:
        dialog["topics"][current_topic] = []
    
    # Add message to topic
    dialog["topics"][current_topic].append(message)
    
    # Save updated dialog
    save_user_dialog(user_id, dialog)

def set_current_topic(user_id: int, topic_name: str = None) -> str:
    """Set the current topic for a user. If topic_name is None, reset to default and return list of topics"""
    dialog = load_user_dialog(user_id)
    
    if topic_name is None:
        # Reset to default topic and return list of topics
        dialog["current_topic"] = DEFAULT_TOPIC
        save_user_dialog(user_id, dialog)
        return list(dialog["topics"].keys())
    else:
        # Set new current topic (create if doesn't exist)
        dialog["current_topic"] = topic_name
        if topic_name not in dialog["topics"]:
            dialog["topics"][topic_name] = []
        save_user_dialog(user_id, dialog)
        return f"Текущая тема установлена: {topic_name}"

def get_last_messages(user_id: int, count: int = 15) -> List[Dict]:
    """Get the last N messages from the current topic for a user"""
    dialog = load_user_dialog(user_id)
    current_topic = dialog.get("current_topic", DEFAULT_TOPIC)
    
    # If current topic doesn't exist, fall back to default
    if current_topic not in dialog["topics"]:
        current_topic = DEFAULT_TOPIC
        # Ensure default topic exists
        if current_topic not in dialog["topics"]:
            dialog["topics"][current_topic] = []
    
    messages = dialog["topics"][current_topic]
    return messages[-count:] if len(messages) > count else messages