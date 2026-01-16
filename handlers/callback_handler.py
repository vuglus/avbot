import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.dialog_service import load_user_dialog, save_user_dialog, DEFAULT_TOPIC, set_current_topic
from handlers.base_handler import BaseHandler


class CallbackHandler(BaseHandler):
    """Handle callback queries from inline buttons"""
    
    async def handle_authorized(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        data = query.data
        
        if data.startswith("topic:"):
            topic_name = data.split(":", 1)[1]
            await self._handle_topic_selection(query, user_id, topic_name)
        elif data == "back_to_topics":
            await self._show_topic_list(query, user_id)
    
    async def _handle_topic_selection(self, query, user_id: int, topic_name: str):
        """Handle topic selection from inline buttons"""
        # Update the user's current topic using existing function
        set_current_topic(user_id, topic_name)
        
        if topic_name == DEFAULT_TOPIC:
            # Show list of all topics when in default mode
            await self._show_topic_list(query, user_id)
        else:
            # Show "back to topics" button when in a specific topic
            keyboard = [[InlineKeyboardButton("Назад к темам", callback_data="back_to_topics")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            try:
                await query.edit_message_text(
                    text=f"Вы выбрали тему: {topic_name}\n\nТеперь все сообщения будут относиться к этой теме.",
                    reply_markup=reply_markup
                )
            except Exception as e:
                # If editing fails, send a new message
                await query.message.reply_text(
                    text=f"Вы выбрали тему: {topic_name}\n\nТеперь все сообщения будут относиться к этой теме.",
                    reply_markup=reply_markup
                )
    
    async def _show_topic_list(self, query, user_id: int):
        """Show the list of available topics with inline buttons"""
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
        
        try:
            await query.edit_message_text(
                text="Выберите тему для общения:",
                reply_markup=reply_markup
            )
        except Exception as e:
            # If editing fails, send a new message
            await query.message.reply_text(
                text="Выберите тему для общения:",
                reply_markup=reply_markup
            )