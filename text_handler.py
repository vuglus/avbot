import logging
from telegram import Update
from telegram.ext import ContextTypes
from services.yandexgpt_service import ask_yandexgpt
from services.dialog_service import load_user_dialog
from services.config_service import YCLOUD_API_KEY, YCLOUD_FOLDER_ID
from services.yandex_index_service import YandexIndexService
from yandex_cloud_ml_sdk import YCloudML

# Initialize logger
logger = logging.getLogger(__name__)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    user_input = update.message.text or update.message.caption or ""
    logger.info(f"Received text message: {user_input}")
    
    # Get current topic and index ID
    user_id = update.effective_user.id
    dialog_data = load_user_dialog(user_id)
    current_topic = dialog_data.get("current_topic", "default")
    
    # Initialize YandexIndexService to get index ID
    sdk = YCloudML(folder_id=YCLOUD_FOLDER_ID, auth=YCLOUD_API_KEY)
    index_service = YandexIndexService(sdk, YCLOUD_FOLDER_ID)
    index_id = index_service.get_index_id_for_topic(user_id, current_topic)
    
    try:
        reply = ask_yandexgpt(user_input, index_id)
        logger.info("handle_text_message received response from YandexGPT")
        await update.message.reply_text(reply)
    except Exception as e:
        logger.error(f"Error calling YandexGPT: {str(e)}")
        await update.message.reply_text(f"Ошибка: {str(e)}")