import logging
from telegram import Update
from telegram.ext import ContextTypes
from handlers.base_handler import BaseHandler
from services.config_service import Config
from clients.icsclient import ICSClient


class CalendarHandler(BaseHandler):
    def __init__(self, config: Config):
        super().__init__(config)
        self.ics_client = ICSClient(config)

    async def handle_authorized(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        args = context.args
        if len(args) < 2:
            await update.message.reply_text(
                "Использование: /calendar <client_type> <url> [название]\n\n"
                "Пример: /calendar caldav /calendars/__uids__/abc123/calendar Мой календарь"
            )
            return

        client_type = args[0]
        url = args[1]
        name = " ".join(args[2:]) if len(args) > 2 else ""
        chat_id = str(update.effective_chat.id)
        chat_type = "tg"

        success = self.ics_client.register_calendar(
            chat_id=chat_id,
            chat_type=chat_type,
            client_type=client_type,
            url=url,
            name=name,
        )

        if success:
            msg = f"Календарь успешно добавлен!\nТип: {client_type}\nURL: {url}"
            if name:
                msg += f"\nИмя: {name}"
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text(
                "Не удалось добавить календарь. Попробуйте позже."
            )
