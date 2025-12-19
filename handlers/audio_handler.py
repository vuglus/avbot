import logging
from telegram import Update
from telegram.ext import ContextTypes
from services.speech_service import process_audio, process_voice
from services.yandexgpt_service import ask_yandexgpt
from handlers.base_handler import BaseHandler
from services.dialog_service import load_user_dialog
from services.config_service import YCLOUD_API_KEY, YCLOUD_FOLDER_ID
from services.yandex_index_service import YandexIndexService
from yandex_cloud_ml_sdk import YCloudML

class AudioHandler(BaseHandler):
    """Handle audio files"""

    async def handle_authorized(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            # Process audio or voice and get transcript
            if update.message.voice:
                transcript = await process_voice(update, context)
            else:
                transcript = await process_audio(update, context)
            
            # Get user ID
            user_id = update.effective_user.id
            
            # Send transcript to YandexGPT with user ID
            reply = ask_yandexgpt(transcript, user_id)
            await update.message.reply_text(reply)

        except Exception as e:
            self.logger.error(f"Error processing audio message: {str(e)}")
            await update.message.reply_text("Не удалось обработать аудиофайл.")
