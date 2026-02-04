import tempfile
from telegram import Update
from telegram.ext import ContextTypes
from services.yandex_index_service import YandexIndexService
from services.dialog_service import load_user_dialog
from services.config_service import Config
from yandex_cloud_ml_sdk import YCloudML
from handlers.base_handler import BaseHandler

class DocumentHandler(BaseHandler):
    """Handle document attachments"""
    def __init__(self, config: Config):
        super().__init__(config)
        self.config = config

    async def handle_authorized(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        # Получаем текущий топик пользователя
        dialog_data = load_user_dialog(user_id)
        current_topic = dialog_data.get("current_topic", "default")
        
        # Инициализируем YandexIndexService
        sdk = YCloudML(folder_id=self.config.getCloudFolder(), auth=self.config.getCloudKey())
        index_service = YandexIndexService(sdk, self.config.getCloudFolder())
        index_name = index_service.get_index_name(user_id, current_topic)
        
        self.logger.info(f"Using index name: {index_name}")
        user_input = update.message.text or update.message.caption or ""
        self.logger.info(f"Received message with document: {user_input}")

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

            except Exception as e:
                self.logger.error(f"Error processing file: {str(e)}")
                await update.message.reply_text("Не удалось обработать файл.")

            # Загружаем файл в индекс
            try:
                index_service.upload_file_to_index(temp_path, file_name, index_name)
                self.logger.info(f"File uploaded and indexed successfully to {index_name}")
            except Exception as e:
                self.logger.error(f"Error indexing file: {str(e)}")
                # Не прерываем основной поток, просто логируем ошибку
                return
        
        # После успешной индексации файла отвечаем пользователю
        await update.message.reply_text(f"Файл: {file_name} успешно загружен и обработан для индексации.")
        return