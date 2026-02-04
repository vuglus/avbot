import os
from telegram import Update
from telegram.ext import ContextTypes
from services.config_service import Config
from services.speech_service import SpeechService
from services.yandexgpt_service import YandexGPTService
from handlers.base_handler import BaseHandler

class AudioHandler(BaseHandler):
    """Handle audio files"""
    def __init__(self, config: Config, GPTService: YandexGPTService):
        self.GPTService = GPTService
        self.SpeechService = SpeechService(config)
        super().__init__(config)

    async def handle_authorized(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            # Process audio or voice and get transcript
            if update.message.voice:
                transcript = await self.SpeechService.process_voice(update, context)
            else:
                transcript = await self.SpeechService.process_audio(update, context)
            
            # Get user ID
            user_id = update.effective_user.id
            
            # Send transcript to YandexGPT with user ID
            reply = self.GPTService.ask_yandexgpt(transcript, user_id)
            await update.message.reply_text(reply)

        except Exception as e:
            self.logger.error(f"Error processing audio message: {str(e)}")
            await update.message.reply_text("Не удалось обработать аудиофайл.")

