import logging
from telegram import Update
from telegram.ext import ContextTypes
from services.speech_service import process_audio, process_voice
from services.yandexgpt_service import ask_yandexgpt
from handlers.base_handler import BaseHandler


class AudioHandler(BaseHandler):
    """Handle audio files"""

    async def handle_authorized(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            # Process audio or voice and get transcript
            if update.message.voice:
                transcript = await process_voice(update, context)
            else:
                transcript = await process_audio(update, context)
            
            # Send transcript to YandexGPT
            reply = ask_yandexgpt(transcript)
            await update.message.reply_text(reply)

        except Exception as e:
            self.logger.error(f"Error processing audio message: {str(e)}")
            await update.message.reply_text("Не удалось обработать аудиофайл.")
