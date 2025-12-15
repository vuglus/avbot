import logging
from telegram import Update
from telegram.ext import ContextTypes
from services.auth import AuthService


class BaseHandler:
    """Base class for all handlers"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.auth_service = AuthService()
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Base handler method"""
        # Check authorization first
        if not await self.auth_service.is_authorized(update):
            await self.auth_service.send_unauthorized_message(update)
            return
            
        # Call the actual handler implementation
        await self.handle_authorized(update, context)
    
    async def handle_unauthorized(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.handle_unauthorized(update, context)
    
    async def handle_authorized(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler method to be implemented by subclasses for authorized users"""
        raise NotImplementedError("Handler method must be implemented by subclass")