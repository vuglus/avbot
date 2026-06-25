import os
import json
from typing import Dict
from storage.abs_storage import DialogStorage, DEFAULT_TOPIC
import logging

logger = logging.getLogger(__name__)

DIALOGS_DIR = "dialogs"

class FileDialogStorage(DialogStorage):
    """Реализация хранения диалогов в файлах"""
    
    def __init__(self, dialogs_dir: str = DIALOGS_DIR):
        self.dialogs_dir = dialogs_dir
        self.ensure_dialogs_dir()
    
    def ensure_dialogs_dir(self):
        if not os.path.exists(self.dialogs_dir):
            os.makedirs(self.dialogs_dir)
    
    def get_user_dialog_file(self, user_id: int) -> str:
        return os.path.join(self.dialogs_dir, f"{user_id}.json")
    
    def load_dialog(self, user_id: int) -> Dict:
        """Загрузить диалог пользователя из файла"""
        dialog_file = self.get_user_dialog_file(user_id)
        
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
    
    def save_dialog(self, user_id: int, dialog_data: Dict):
        """Сохранить диалог пользователя в файл"""
        dialog_file = self.get_user_dialog_file(user_id)
        try:
            with open(dialog_file, 'w', encoding='utf-8') as f:
                json.dump(dialog_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving dialog for user {user_id}: {str(e)}")

