import os
import json
import logging
from typing import List, Dict, Optional
from abc import ABC, abstractmethod

DIALOGS_DIR = "dialogs"
DEFAULT_TOPIC = "default"

logger = logging.getLogger(__name__)


class DialogStorage(ABC):
    """Абстрактный класс для хранения диалогов"""
    
    @abstractmethod
    def load_dialog(self, user_id: int) -> Dict:
        """Загрузить диалог пользователя"""
        pass
    
    @abstractmethod
    def save_dialog(self, user_id: int, dialog_data: Dict):
        """Сохранить диалог пользователя"""
        pass


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


class YDBDialogStorage(DialogStorage):
    """Заглушка для хранения диалогов в YDB"""
    
    def load_dialog(self, user_id: int) -> Dict:
        """Загрузить диалог пользователя из YDB"""
        # TODO: Реализовать загрузку из YDB
        logger.info(f"Загрузка диалога пользователя {user_id} из YDB")
        return {
            "current_topic": DEFAULT_TOPIC,
            "topics": {
                DEFAULT_TOPIC: {
                    "messages": []
                }
            }
        }
    
    def save_dialog(self, user_id: int, dialog_data: Dict):
        """Сохранить диалог пользователя в YDB"""
        # TODO: Реализовать сохранение в YDB
        logger.info(f"Сохранение диалога пользователя {user_id} в YDB")


class DialogService:
    """Сервис для работы с диалогами пользователей"""
    
    def __init__(self, storage: DialogStorage):
        self.storage = storage
    
    def add_message_to_topic(self, user_id: int, message: Dict, topic_name: str = None):
        """Добавить сообщение в тему диалога"""
        dialog = self.storage.load_dialog(user_id)
        current_topic = topic_name or dialog.get("current_topic", DEFAULT_TOPIC)
        
        if current_topic not in dialog["topics"]:
            dialog["topics"][current_topic] = {"messages": []}
        
        dialog["topics"][current_topic]["messages"].append(message)
        self.storage.save_dialog(user_id, dialog)
    
    def set_current_topic(self, user_id: int, topic_name: str = None) -> str:
        """Установить текущую тему диалога"""
        dialog = self.storage.load_dialog(user_id)
        
        if topic_name is None:
            dialog["current_topic"] = DEFAULT_TOPIC
            self.storage.save_dialog(user_id, dialog)
            return list(dialog["topics"].keys())
        else:
            dialog["current_topic"] = topic_name
            if topic_name not in dialog["topics"]:
                dialog["topics"][topic_name] = {"messages": []}
            self.storage.save_dialog(user_id, dialog)
            return f"Текущая тема установлена: {topic_name}"
    
    def get_last_messages(self, user_id: int, count: int = 15, topic_name: str = None) -> List[Dict]:
        """Получить последние сообщения из темы диалога"""
        dialog = self.storage.load_dialog(user_id)
        current_topic = topic_name or dialog.get("current_topic", DEFAULT_TOPIC)
        
        if current_topic not in dialog["topics"]:
            current_topic = DEFAULT_TOPIC
            if current_topic not in dialog["topics"]:
                dialog["topics"][current_topic] = {"messages": []}
        
        messages = dialog["topics"][current_topic]["messages"]
        return messages[-count:] if len(messages) > count else messages
    
    def set_topic_index(self, user_id: int, topic_name: str, index_id: str):
        """Установить идентификатор индекса для темы"""
        dialog = self.storage.load_dialog(user_id)
        
        if topic_name not in dialog["topics"]:
            dialog["topics"][topic_name] = {"messages": []}
        
        dialog["topics"][topic_name]["index_id"] = index_id
        self.storage.save_dialog(user_id, dialog)
