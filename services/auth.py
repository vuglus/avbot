from telegram import Update
from services.config_service import Config


class AuthService:
    """Authorization service for checking user access"""
    def __init__(self, config: Config):
        self.config = config
        pass
    
    async def is_authorized(self, update: Update) -> bool:
        """Check if the user is authorized"""
        # If whitelist is empty, allow all users
        if not self.config.getBotWhitelist():
            return True
        
        # If whitelist is not empty, check if user is in whitelist
        if not update.effective_user:
            return True
            
        # Get user ID from update
        user_id = None
        if update.effective_user:
            user_id = update.effective_user.id
            
        # Check if user is in whitelist
        return user_id in self.config.getBotWhitelist()
    
    async def send_unauthorized_message(self, update: Update):
        """Send unauthorized access message to user"""
        await update.message.reply_text("Извините, у вас нет доступа к этому боту. Уточните свой ИД у бота (https://t.me/userinfobot) и пришлите его @avinogradov")
        