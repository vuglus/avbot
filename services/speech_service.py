import tempfile
import logging
import os
from telegram import Update
from telegram.ext import ContextTypes
from pydub import AudioSegment
from services.speech import recognize_speech
from services.config_service import Config

# Initialize logger
logger = logging.getLogger(__name__)

# Directory for saving audio files for analysis
UPLOADS_DIR = "uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)

class SpeechService:
    def __init__(self, config: Config):
        self.config = config

    def convert_audio(file_name):
        # Save a copy to uploads directory for analysis
        uploads_path = os.path.join(UPLOADS_DIR, os.path.basename(file_name))
        with open(file_name, 'rb') as src, open(uploads_path, 'wb') as dst:
            dst.write(src.read())
        logger.info(f"Saved audio file to: {uploads_path}")

        if uploads_path.endswith('.oga'):
            return uploads_path

        output_path = uploads_path + ".ogg"

        logger.info(f"convert audio file from {uploads_path} to: {output_path}")
        """Convert audio file to OGG format with required specifications"""
        sound = AudioSegment.from_file(uploads_path).set_frame_rate(16000).set_channels(1)
        sound.export(output_path, format="ogg")

        return output_path

    async def process_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process audio files and return recognized text"""
        audio = update.message.audio
        file_name = audio.file_name or "audio.mp3"
        logger.info(f"Received audio file: {file_name}")

        try:
            file = await audio.get_file()
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                await file.download_to_drive(custom_path=temp_file.name)
                temp_path = temp_file.name

            ogg_path = self.convert_audio(temp_path)

            # Recognize speech using Yandex SpeechKit
            try:
                transcript = recognize_speech(ogg_path, config.getCloudKey(), config.getCloudFolder())
            except Exception as e:
                logger.error(f"Error recognizing speech: {str(e)}")
                transcript = "Не удалось распознать речь"

            logger.info(f"Recognized text from audio: {transcript}")
            return transcript

        except Exception as e:
            logger.error(f"Error processing audio: {str(e)}")
            raise Exception("Не удалось обработать аудиофайл.")


    async def process_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process voice messages and return recognized text"""
        voice = update.message.voice
        logger.info("Received voice message")

        try:
            file = await voice.get_file()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".oga") as temp_file:
                await file.download_to_drive(custom_path=temp_file.name)
                temp_path = temp_file.name

            ogg_path = self.convert_audio(temp_path)

            # Recognize speech using Yandex SpeechKit
            try:
                transcript = recognize_speech(ogg_path, config.getCloudKey(), config.getCloudFolder())
            except Exception as e:
                logger.error(f"Error recognizing speech: {str(e)}")
                transcript = "Не удалось распознать речь"

            logger.info(f"Recognized text from voice: {transcript}")
            return transcript

        except Exception as e:
            logger.error(f"Error processing voice: {str(e)}")
            raise Exception("Не удалось обработать голосовое сообщение.")