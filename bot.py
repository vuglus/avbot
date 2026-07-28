import os
import logging
import asyncio
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from services.config_service import Config, load_config
from services.yandexgpt_service import YandexGPTService
from handlers.start_handler import StartHandler
from handlers.text_handler import TextHandler
from handlers.document_handler import DocumentHandler
from handlers.audio_handler import AudioHandler
from handlers.topic_handler import TopicHandler
from handlers.callback_handler import CallbackHandler
from handlers.calendar_handler import CalendarHandler
from handlers.calendars_handler import CalendarsHandler
from services.dialog_service import DialogService
from storage.file_storage import FileDialogStorage, DIALOGS_DIR
from yandex_ai_studio_sdk import AIStudio
from services.yandex_index_service import YandexIndexService
from services.api_server import ApiServer

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

CONFIG_PATH = os.environ.get("CONFIG_PATH", "./config/config.yml")
DIALOGS_PATH = os.environ.get("DIALOGS_PATH", DIALOGS_DIR)
config = Config(load_config(CONFIG_PATH))

# Build and run the bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(config.getBotToken()).build()

    # Create dialog service instance
    dialog_service = DialogService(FileDialogStorage(DIALOGS_PATH))

    # Create Yandex Index Service instance
    yandex_sdk = AIStudio(auth=config.getCloudKey(), folder_id=config.getCloudFolder())
    index_service = YandexIndexService(
        yandex_sdk, config.getCloudFolder(), dialog_service
    )

    # Create handler instances
    start_handler = StartHandler(config)
    text_handler = TextHandler(config, YandexGPTService(config), dialog_service)
    document_handler = DocumentHandler(config)
    audio_handler = AudioHandler(config, YandexGPTService(config))
    topic_handler = TopicHandler(config, dialog_service)
    callback_handler = CallbackHandler(config, dialog_service)
    calendar_handler = CalendarHandler(config)
    calendars_handler = CalendarsHandler(config)

    # Register handlers
    app.add_handler(CommandHandler("start", start_handler.handle_unauthorized))
    app.add_handler(CommandHandler("topic", topic_handler.handle))
    app.add_handler(CommandHandler("calendar", calendar_handler.handle))
    app.add_handler(CommandHandler("calendars", calendars_handler.handle))
    app.add_handler(CallbackQueryHandler(callback_handler.handle))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler.handle)
    )
    app.add_handler(MessageHandler(filters.Document.ALL, document_handler.handle))
    app.add_handler(MessageHandler(filters.AUDIO | filters.VOICE, audio_handler.handle))

    # Initialize and start background services
    async def start_background_services(application):
        # Start API server
        api_key = config.get("api", "api_key", "")
        api_port = config.get("api", "port", 5200)
        if api_key:
            api_server = ApiServer(
                api_key=api_key,
                bot=application.bot,
                port=api_port,
                config=config,
                logger=logger.getChild("api"),
            )
            asyncio.create_task(api_server.getTask())
            logger.info("API server started on port %s", api_port)
        else:
            logger.warning("API key not configured — API server not started")

    print("Бот запущен...")
    # Start background services
    app.post_init = start_background_services
    app.run_polling()
