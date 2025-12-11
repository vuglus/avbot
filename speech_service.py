import tempfile
import logging
from telegram import Update
from telegram.ext import ContextTypes
from pydub import AudioSegment
from speech import recognize_speech
from services.config_service import YCLOUD_API_KEY, YCLOUD_FOLDER_ID

# Initialize logger
logger = logging.getLogger(__name__)


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

        # Convert and recognize
        wav_path = temp_path + ".mp3"
        sound = AudioSegment.from_mp3(temp_path).set_frame_rate(16000).set_channels(1)
        sound.export(wav_path, format="mp3")

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