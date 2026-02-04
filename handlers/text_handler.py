from telegram import Update
from telegram.ext import ContextTypes
from services.yandexgpt_service import YandexGPTService
from handlers.base_handler import BaseHandler
from services.dialog_service import add_message_to_topic, get_last_messages
from services.config_service import Config

class TextHandler(BaseHandler):
    """Handle text messages"""
    def __init__(self, config: Config, gpt: YandexGPTService):
        super().__init__(config)
        self.gpt = gpt
    
    async def handle_authorized(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_input = update.message.text or update.message.caption or ""
        self.logger.info(f"Received text message: {user_input}")
        
        # Add user message to dialog history
        add_message_to_topic(user_id, {"role": "user", "text": user_input})
        
        # Get last 15 messages for context
        dialog_context = get_last_messages(user_id, 15)
        
        try:
            reply = self.gpt.ask_yandexgpt_with_context(user_input, dialog_context, user_id)
            self.logger.info("TextHandler received response from YandexGPT")
            
            # Add assistant message to dialog history
            add_message_to_topic(user_id, {"role": "assistant", "text": reply})
            
            await update.message.reply_text(reply)
        except Exception as e:
            self.logger.error(f"Error calling YandexGPT: {str(e)} user_input: {user_input} dialog_context: {dialog_context}")
            await update.message.reply_text(f"Ошибка: {str(e)}")