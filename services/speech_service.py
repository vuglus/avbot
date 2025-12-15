import tempfile
import logging
import os
from telegram import Update
from telegram.ext import ContextTypes
from pydub import AudioSegment
from speech import recognize_speech
from services.config_service import YCLOUD_API_KEY, YCLOUD_FOLDER_ID

# Initialize logger
logger = logging.getLogger(__name__)

# Directory for saving audio files for analysis
UPLOADS_DIR = "uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)


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

        # Save a copy to uploads directory for analysis
        uploads_path = os.path.join(UPLOADS_DIR, file_name)
        with open(temp_path, 'rb') as src, open(uploads_path, 'wb') as dst:
            dst.write(src.read())
        logger.info(f"Saved audio file to: {uploads_path}")

        # Convert and recognize
        wav_path = temp_path + ".wav"
        sound = AudioSegment.from_mp3(temp_path).set_frame_rate(16000).set_channels(1)
        sound.export(wav_path, format="wav")

        # Recognize speech using Yandex SpeechKit
        try:
            transcript = recognize_speech(wav_path, YCLOUD_API_KEY, YCLOUD_FOLDER_ID)
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

        # Save a copy to uploads directory for analysis
        uploads_path = os.path.join(UPLOADS_DIR, f"voice_{int(voice.file_id[-6:], 16) % 1000000}.oga")
        with open(temp_path, 'rb') as src, open(uploads_path, 'wb') as dst:
            dst.write(src.read())
        logger.info(f"Saved voice file to: {uploads_path}")

        # Convert OGA to WAV for recognition
        wav_path = temp_path + ".wav"
        sound = AudioSegment.from_ogg(temp_path).set_frame_rate(16000).set_channels(1)
        sound.export(wav_path, format="wav")

        # Recognize speech using Yandex SpeechKit
        try:
            transcript = recognize_speech(wav_path, YCLOUD_API_KEY, YCLOUD_FOLDER_ID)
        except Exception as e:
            logger.error(f"Error recognizing speech: {str(e)}")
            transcript = "Не удалось распознать речь"

        logger.info(f"Recognized text from voice: {transcript}")
        return transcript

    except Exception as e:
        logger.error(f"Error processing voice: {str(e)}")
        raise Exception("Не удалось обработать голосовое сообщение.")