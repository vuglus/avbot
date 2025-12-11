from telegram import Update
from config import WHITELIST


class AuthService:
    """Authorization service for checking user access"""
    
    @staticmethod
    async def is_authorized(update: Update) -> bool:
        """Check if the user is authorized"""
        # If whitelist is empty, allow all users
        if not WHITELIST:
            return True
            
        # Get user ID from update
        user_id = None
        if update.effective_user:
            user_id = update.effective_user.id
            
        # Check if user is in whitelist
        return user_id in WHITELIST
    
    @staticmethod
    async def send_unauthorized_message(update: Update):
        """Send unauthorized access message to user"""
        await update.message.reply_text("Извините, у вас нет доступа к этому боту.")