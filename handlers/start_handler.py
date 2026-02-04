from telegram import Update
from telegram.ext import ContextTypes
from handlers.base_handler import BaseHandler
from services.config_service import Config

class StartHandler(BaseHandler):
    def __init__(self, config: Config):
        self.config = config
    
    async def handle_unauthorized(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(self.config.getBot('welcome'))
