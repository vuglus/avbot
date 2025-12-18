import logging
from telegram import Update
from telegram.ext import ContextTypes
from services.yandexgpt_service import ask_yandexgpt

# Initialize logger
logger = logging.getLogger(__name__)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    user_input = update.message.text or update.message.caption or ""
    logger.info(f"Received text message: {user_input}")
    
    try:
        reply = ask_yandexgpt(user_input)
        logger.info("handle_text_message received response from YandexGPT")
        await update.message.reply_text(reply)
    except Exception as e:
        logger.error(f"Error calling YandexGPT: {str(e)}")
        await update.message.reply_text(f"Ошибка: {str(e)}")