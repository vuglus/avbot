import os
import tempfile
import logging
from telegram import Update
from telegram.ext import ContextTypes
from services.yandexgpt_service import ask_yandexgpt

# Initialize logger
logger = logging.getLogger(__name__)


async def handle_document_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle document attachments"""
    user_input = update.message.text or update.message.caption or ""
    logger.info(f"Received message with document: {user_input}")
    file_text = ""

    # Check if there's a document
    if update.message.document:
        document = update.message.document
        file_name = document.file_name.lower()
        logger.info(f"Detected file: {file_name} Document type: {update.message.document.mime_type}")

        try:
            file = await document.get_file()
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                await file.download_to_drive(custom_path=temp_file.name)
                temp_path = temp_file.name

            if file_name.endswith(".txt"):
                with open(temp_path, "r", encoding="utf-8") as f:
                    file_text = f.read()
                    logger.info(f"Text file read, text length: {len(file_text)} characters")
            else:
                await update.message.reply_text("Поддерживаются только файлы .txt и .mp3")
                return

        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            await update.message.reply_text("Не удалось обработать файл.")
            return
    
    # Combine request text and file content
    full_prompt = user_input.strip()
    if file_text:
        full_prompt += "\n\n" + file_text.strip()

    logger.info(f"Constructed prompt (length: {len(full_prompt)}):\n{full_prompt[:200]}...")

    try:
        reply = ask_yandexgpt(full_prompt)
        logger.info("Received response from YandexGPT")
        await update.message.reply_text(reply)
    except Exception as e:
        logger.error(f"Error calling YandexGPT: {str(e)}")
        await update.message.reply_text(f"Ошибка: {str(e)}")