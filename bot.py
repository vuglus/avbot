import os
import logging
import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from services.config_service import Config, load_config
from services.yandexgpt_service import YandexGPTService
from handlers.start_handler import StartHandler
from handlers.text_handler import TextHandler
from handlers.document_handler import DocumentHandler
from handlers.audio_handler import AudioHandler
from handlers.topic_handler import TopicHandler
from handlers.callback_handler import CallbackHandler
from clients.icsclient import ICSClient
from handlers.icshandler import ICSHandler
from services.dialog_service import DialogService
from storage.file_storage import FileDialogStorage, DIALOGS_DIR
from yandex_ai_studio_sdk import AIStudio
from services.yandex_index_service import YandexIndexService

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

CONFIG_PATH = os.environ.get('CONFIG_PATH', './config/config.yml')
DIALOGS_PATH = os.environ.get('DIALOGS_PATH', DIALOGS_DIR)
config = Config(load_config(CONFIG_PATH))

# Build and run the bot
if __name__ == '__main__':
    app = ApplicationBuilder().token(config.getBotToken()).build()
    
    # Create dialog service instance
    dialog_service = DialogService(FileDialogStorage(DIALOGS_PATH))
    
    # Create Yandex Index Service instance
    yandex_sdk = AIStudio(
        auth=config.getCloudKey(),
        folder_id=config.getCloudFolder()
    )
    index_service = YandexIndexService(yandex_sdk, config.getCloudFolder(), dialog_service)
    
    # Create handler instances
    start_handler = StartHandler(config)
    text_handler = TextHandler(config, YandexGPTService(config), dialog_service)
    document_handler = DocumentHandler(config)
    audio_handler = AudioHandler(config, YandexGPTService(config))
    topic_handler = TopicHandler(config, dialog_service)
    callback_handler = CallbackHandler(config, dialog_service)

    # Register handlers
    app.add_handler(CommandHandler("start", start_handler.handle_unauthorized))
    app.add_handler(CommandHandler("topic", topic_handler.handle))
    app.add_handler(CallbackQueryHandler(callback_handler.handle))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler.handle))
    app.add_handler(MessageHandler(filters.Document.ALL, document_handler.handle))
    app.add_handler(MessageHandler(filters.AUDIO | filters.VOICE, audio_handler.handle))

    # Initialize and start ICS monitoring
    async def start_ics_monitoring(application):
        ics_client = ICSClient(config)
        ics_handler = ICSHandler(config, application.bot)
        # Start monitoring in the background
        asyncio.create_task(ics_handler.monitor_loop(ics_client))
      
    print("Бот запущен...")
    # Start ICS monitoring
    app.post_init = start_ics_monitoring
    app.run_polling()
