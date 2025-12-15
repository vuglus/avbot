from telegram import Update
from telegram.ext import ContextTypes
from handlers.base_handler import BaseHandler
from services.config_service import BOT_WELCOME

class StartHandler(BaseHandler):
    """Handle the /start command"""
    
    async def handle_unauthorized(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(BOT_WELCOME)
