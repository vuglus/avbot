
from typing import Dict
from abc import ABC, abstractmethod

DEFAULT_TOPIC = "default"

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

