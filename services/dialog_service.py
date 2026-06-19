import logging
from typing import List, Dict
from storage.abs_storage import DialogStorage, DEFAULT_TOPIC

logger = logging.getLogger(__name__)

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
