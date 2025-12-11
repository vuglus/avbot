import os
import tempfile
import logging
from telegram import Update
from telegram.ext import ContextTypes
from yandexgpt_service import ask_yandexgpt
from handlers.base_handler import BaseHandler


class DocumentHandler(BaseHandler):
    """Handle document attachments"""
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_input = update.message.text or update.message.caption or ""
        self.logger.info(f"Received message with document: {user_input}")
        file_text = ""

        # Check if there's a document
        if update.message.document:
            document = update.message.document
            file_name = document.file_name.lower()
            self.logger.info(f"Detected file: {file_name} Document type: {update.message.document.mime_type}")

            try:
                file = await document.get_file()
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    await file.download_to_drive(custom_path=temp_file.name)
                    temp_path = temp_file.name

                if file_name.endswith(".txt"):
                    with open(temp_path, "r", encoding="utf-8") as f:
                        file_text = f.read()
                        self.logger.info(f"Text file read, text length: {len(file_text)} characters")
                else:
                    await update.message.reply_text("Поддерживаются только файлы .txt и .mp3")
                    return

            except Exception as e:
                self.logger.error(f"Error processing file: {str(e)}")
                await update.message.reply_text("Не удалось обработать файл.")
                return
        
        # Combine request text and file content
        full_prompt = user_input.strip()
        if file_text:
            full_prompt += "\n\n" + file_text.strip()

        self.logger.info(f"Constructed prompt (length: {len(full_prompt)}):\n{full_prompt[:200]}...")

        try:
            reply = ask_yandexgpt(full_prompt)
            self.logger.info("Received response from YandexGPT")
            await update.message.reply_text(reply)
        except Exception as e:
            self.logger.error(f"Error calling YandexGPT: {str(e)}")
            await update.message.reply_text(f"Ошибка при обращении к YandexGPT: {str(e)}")