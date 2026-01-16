import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.dialog_service import set_current_topic, load_user_dialog, DEFAULT_TOPIC
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
            
            if topic_name == "default":
                # Show list of topics with buttons
                await self._show_topic_buttons(update, user_id)
            else:
                # Show "back to topics" button
                keyboard = [[InlineKeyboardButton("Назад к темам", callback_data="back_to_topics")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(response, reply_markup=reply_markup)
        else:
            # Show list of topics with buttons
            await self._show_topic_buttons(update, user_id)
    
    async def _show_topic_buttons(self, update: Update, user_id: int):
        """Show topic selection buttons"""
        dialog = load_user_dialog(user_id)
        # Filter out "default" from the topic list
        topics = [topic for topic in dialog["topics"].keys() if topic != DEFAULT_TOPIC]
        
        # Create buttons for each topic
        keyboard = [
            [InlineKeyboardButton(topic, callback_data=f"topic:{topic}")]
            for topic in topics
        ]
        
        # Add "default" button separately
        keyboard.append([InlineKeyboardButton("default", callback_data="topic:default")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text("Выберите тему для общения:", reply_markup=reply_markup)