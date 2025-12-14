import logging
from telegram import Update
from telegram.ext import ContextTypes
from services.dialog_service import set_current_topic
from handlers.base_handler import BaseHandler


class TopicHandler(BaseHandler):
    """Handle /topic command"""
    
    async def handle_authorized(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        message_text = update.message.text or ""
        
        # Extract topic name (if provided)
        topic_name = message_text[len("/topic "):].strip() if message_text.startswith("/topic ") else None
        
        if topic_name:
            # Set the current topic
            response = set_current_topic(user_id, topic_name)
            await update.message.reply_text(response)
        else:
            # Show list of topics and reset to default
            topics = set_current_topic(user_id, None)
            response = "Список доступных тем:\n" + "\n".join(f"- {topic}" for topic in topics)
            response += "\n\nТекущая тема сброшена на 'default'"
            await update.message.reply_text(response)