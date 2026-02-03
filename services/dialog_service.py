import os
import json
import logging
from typing import List, Dict

DIALOGS_DIR = "dialogs"
DEFAULT_TOPIC = "default"

logger = logging.getLogger(__name__)

def ensure_dialogs_dir():
    if not os.path.exists(DIALOGS_DIR):
        os.makedirs(DIALOGS_DIR)

def get_user_dialog_file(user_id: int) -> str:
    return os.path.join(DIALOGS_DIR, f"{user_id}.json")

def load_user_dialog(user_id: int) -> Dict:
    """Load a user's dialog data, supporting old format"""
    dialog_file = get_user_dialog_file(user_id)
    
    default_structure = {
        "current_topic": DEFAULT_TOPIC,
        "topics": {
            DEFAULT_TOPIC: {
                "messages": []
            }
        }
    }

    if not os.path.exists(dialog_file):
        return default_structure
    
    try:
        with open(dialog_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Преобразуем старую структуру (список сообщений) в новую
        for topic_name, content in list(data.get("topics", {}).items()):
            if isinstance(content, list):
                data["topics"][topic_name] = {"messages": content}
            elif "messages" not in content:
                data["topics"][topic_name]["messages"] = []

        # Убедимся, что current_topic существует
        current_topic = data.get("current_topic", DEFAULT_TOPIC)
        if current_topic not in data["topics"]:
            data["topics"][current_topic] = {"messages": []}
        data["current_topic"] = current_topic
        
        # Убедимся, что DEFAULT_TOPIC существует
        if DEFAULT_TOPIC not in data["topics"]:
            data["topics"][DEFAULT_TOPIC] = {"messages": []}

        return data

    except Exception as e:
        logger.error(f"Error loading dialog for user {user_id}: {str(e)}")
        return default_structure

def save_user_dialog(user_id: int, dialog_data: Dict):
    ensure_dialogs_dir()
    dialog_file = get_user_dialog_file(user_id)
    try:
        with open(dialog_file, 'w', encoding='utf-8') as f:
            json.dump(dialog_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving dialog for user {user_id}: {str(e)}")

def add_message_to_topic(user_id: int, message: Dict, topic_name: str = None):
    dialog = load_user_dialog(user_id)
    current_topic = topic_name or dialog.get("current_topic", DEFAULT_TOPIC)
    
    if current_topic not in dialog["topics"]:
        dialog["topics"][current_topic] = {"messages": []}
    
    dialog["topics"][current_topic]["messages"].append(message)
    save_user_dialog(user_id, dialog)

def set_current_topic(user_id: int, topic_name: str = None) -> str:
    dialog = load_user_dialog(user_id)
    
    if topic_name is None:
        dialog["current_topic"] = DEFAULT_TOPIC
        save_user_dialog(user_id, dialog)
        return list(dialog["topics"].keys())
    else:
        dialog["current_topic"] = topic_name
        if topic_name not in dialog["topics"]:
            dialog["topics"][topic_name] = {"messages": []}
        save_user_dialog(user_id, dialog)
        return f"Текущая тема установлена: {topic_name}"

def get_last_messages(user_id: int, count: int = 15, topic_name: str = None) -> List[Dict]:
    dialog = load_user_dialog(user_id)
    current_topic = topic_name or dialog.get("current_topic", DEFAULT_TOPIC)
    
    if current_topic not in dialog["topics"]:
        current_topic = DEFAULT_TOPIC
        if current_topic not in dialog["topics"]:
            dialog["topics"][current_topic] = {"messages": []}
    
    messages = dialog["topics"][current_topic]["messages"]
    return messages[-count:] if len(messages) > count else messages

def set_topic_index(user_id: int, topic_name: str, index_id: str):
    """Set the index_id for a specific topic"""
    dialog = load_user_dialog(user_id)
    
    if topic_name not in dialog["topics"]:
        dialog["topics"][topic_name] = {"messages": []}
    
    dialog["topics"][topic_name]["index_id"] = index_id
    save_user_dialog(user_id, dialog)
