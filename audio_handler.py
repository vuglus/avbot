import logging
from telegram import Update
from telegram.ext import ContextTypes
from services.speech_service import process_audio
from services.yandexgpt_service import ask_yandexgpt

# Initialize logger
logger = logging.getLogger(__name__)


async def handle_audio_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle audio files"""
    try:
        # Process audio and get transcript
        transcript = await process_audio(update, context)
        
        # Send transcript to YandexGPT
        reply = ask_yandexgpt(transcript)
        await update.message.reply_text(reply)

    except Exception as e:
        logger.error(f"Error processing audio message: {str(e)}")
        await update.message.reply_text("Не удалось обработать аудиофайл.")