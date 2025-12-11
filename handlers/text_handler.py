import logging
from telegram import Update
from telegram.ext import ContextTypes
from yandexgpt_service import ask_yandexgpt
from handlers.base_handler import BaseHandler


class TextHandler(BaseHandler):
    """Handle text messages"""
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_input = update.message.text or update.message.caption or ""
        self.logger.info(f"Received text message: {user_input}")
        
        try:
            reply = ask_yandexgpt(user_input)
            self.logger.info("Received response from YandexGPT")
            await update.message.reply_text(reply)
        except Exception as e:
            self.logger.error(f"Error calling YandexGPT: {str(e)}")
            await update.message.reply_text(f"Ошибка при обращении к YandexGPT: {str(e)}")