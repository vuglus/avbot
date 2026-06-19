import logging
from typing import Dict
from storage.abs_storage import DialogStorage, DEFAULT_TOPIC

logger = logging.getLogger(__name__)

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
