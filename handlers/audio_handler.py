import logging
from telegram import Update
from telegram.ext import ContextTypes
from speech_service import process_audio
from yandexgpt_service import ask_yandexgpt
from handlers.base_handler import BaseHandler


class AudioHandler(BaseHandler):
    """Handle audio files"""
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            # Process audio and get transcript
            transcript = await process_audio(update, context)
            
            # Send transcript to YandexGPT
            reply = ask_yandexgpt(transcript)
            await update.message.reply_text(reply)

        except Exception as e:
            self.logger.error(f"Error processing audio message: {str(e)}")
            await update.message.reply_text("Не удалось обработать аудиофайл.")