from telegram import Update
from telegram.ext import ContextTypes
from handlers.base_handler import BaseHandler


class StartHandler(BaseHandler):
    """Handle the /start command"""
    
    async def handle_authorized(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Привет! Напиши мне что-нибудь, и я задам это YandexGPT через YCloudML.")