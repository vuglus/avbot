import logging
from telegram import Update
from telegram.ext import ContextTypes


class BaseHandler:
    """Base class for all handlers"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Base handler method to be implemented by subclasses"""
        raise NotImplementedError("Handler method must be implemented by subclass")