import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from yandex_cloud_ml_sdk import YCloudML
from yandex_speechkit import SpeechKit
from pydub import AudioSegment
import tempfile
import logging

# Загружаем переменные окружения
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
YCLOUD_API_KEY = os.getenv("YCLOUD_API_KEY")
YCLOUD_FOLDER_ID = os.getenv("YCLOUD_FOLDER_ID")
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT")
SPEECHKIT_API_KEY = os.getenv("SPEECHKIT_API_KEY")
speechkit = SpeechKit(api_key=SPEECHKIT_API_KEY)

# Инициализация YCloudML
sdk = YCloudML(folder_id=YCLOUD_FOLDER_ID, auth=YCLOUD_API_KEY)
model = sdk.models.completions("yandexgpt", model_version="rc").configure(temperature=0.3)

# Запрос к YandexGPT через YCloudML
def ask_yandexgpt(prompt: str) -> str:
    result = model.run([
        {"role": "system", "text": SYSTEM_PROMPT},
        {"role": "user", "text": prompt}
    ])
    
    if result and result.alternatives:
        return result.alternatives[0].text
    else:
        return "Ответ от YandexGPT пустой или в неожиданном формате."


# 🚀 Обработка сообщений с текстом и, возможно, прикреплённым текстовым файлом
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text or ""
    file_text = ""

    # Есть ли документ?
    if update.message.document:
        document = update.message.document
        logger.info(f"Обнаружен файл: {document.file_name}")
        if document.file_name.endswith(".txt"):
            try:
                file = await document.get_file()
                downloaded_file = await file.download_to_drive()
                logger.info(f"Файл скачан: {downloaded_file.name}")
                with open(downloaded_file.name, 'r', encoding='utf-8') as f:
                    file_text = f.read()
                    logger.info(f"Файл прочитан, длина текста: {len(file_text)} символов")
            except Exception as e:
                logger.error(f"Ошибка при скачивании/чтении файла: {str(e)}")
                await update.message.reply_text("Не удалось обработать файл.")
                return
        elif file_name.endswith(".mp3"):
            # Конвертируем MP3 → WAV (SpeechKit требует wav 16kHz mono)
            wav_path = temp_path + ".wav"
            sound = AudioSegment.from_mp3(temp_path).set_frame_rate(16000).set_channels(1)
            sound.export(wav_path, format="wav")
            logger.info(f"Файл .mp3 сконвертирован в .wav")

            # Распознавание
            transcript = speechkit.recognize(wav_path)
            logger.info(f"Распознанный текст: {transcript}")
            file_text = transcript
        else:
            logger.warning("Файл с неподдерживаемым расширением")
            await update.message.reply_text("Пожалуйста, прикладывайте только .txt файлы.")
            return

    # Объединяем текст запроса и файл
    full_prompt = user_input.strip() + "\n\n" + file_text.strip()
    logger.info(f"Собранный prompt (длина: {len(full_prompt)}):\n{full_prompt[:200]}...")

    try:
        reply = ask_yandexgpt(full_prompt)
        await update.message.reply_text(reply)
    except Exception as e:
        logger.error(f"Ошибка при обращении к YandexGPT: {str(e)}")
        await update.message.reply_text(f"Ошибка при обращении к YandexGPT: {str(e)}")

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Напиши мне что-нибудь, и я задам это YandexGPT через YCloudML.")

# Настраиваем логи
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Запуск бота
if __name__ == '__main__':    
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_message))  # обработка сообщений с вложениями

    print("Бот запущен...")
    app.run_polling()
