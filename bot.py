import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from services.config_service import BOT_TOKEN
from handlers.start_handler import StartHandler
from handlers.text_handler import TextHandler
from handlers.document_handler import DocumentHandler
from handlers.audio_handler import AudioHandler
from handlers.topic_handler import TopicHandler
from handlers.callback_handler import CallbackHandler

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Build and run the bot
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Create handler instances
    start_handler = StartHandler()
    text_handler = TextHandler()
    document_handler = DocumentHandler()
    audio_handler = AudioHandler()
    topic_handler = TopicHandler()
    callback_handler = CallbackHandler()

    # Register handlers
    app.add_handler(CommandHandler("start", start_handler.handle_unauthorized))
    app.add_handler(CommandHandler("topic", topic_handler.handle))
    app.add_handler(CallbackQueryHandler(callback_handler.handle))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler.handle))
    app.add_handler(MessageHandler(filters.Document.ALL, document_handler.handle))
    app.add_handler(MessageHandler(filters.AUDIO | filters.VOICE, audio_handler.handle))

    print("Бот запущен...")
    app.run_polling()
