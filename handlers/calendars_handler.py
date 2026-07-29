import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
from handlers.base_handler import BaseHandler
from services.config_service import Config
from clients.icsclient import ICSClient
import md2tgmd


EDITABLE_FIELDS = {"name", "url", "client_type", "timezone"}
SKILL_FILE = Path(__file__).resolve().parent.parent / "skills" / "calendar.md"
INFO_FILE = Path(__file__).resolve().parent.parent / "skills" / "calendar_info.md"


class CalendarsHandler(BaseHandler):
    def __init__(self, config: Config):
        super().__init__(config)
        self.ics_client = ICSClient(config)

    async def handle_authorized(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        args = context.args
        chat_id = str(update.effective_chat.id)

        if not args:
            await self._list_calendars(update, chat_id)
            return

        sub = args[0]
        if sub == "del" and len(args) >= 2:
            await self._delete_calendar(update, args[1], chat_id)
        elif sub == "edit" and len(args) >= 4:
            await self._edit_calendar(
                update, args[1], args[2], " ".join(args[3:]), chat_id
            )
        elif sub == "edit" and len(args) >= 3:
            await self._edit_calendar(update, args[1], args[2], "", chat_id)
        elif sub == "event" and len(args) >= 3:
            await self._create_event(update, args[1], " ".join(args[2:]), chat_id)
        elif sub == "add":
            await self._add_calendar(update, args[1:], chat_id)
        elif sub == "info":
            await self._send_info(update)
        elif sub == "help":
            await self._send_help(update)
        else:
            await self._send_help(update)

    async def _send_help(self, update: Update):
        try:
            text = SKILL_FILE.read_text(encoding="utf-8")
            await update.message.reply_text(
                md2tgmd.escape(text), parse_mode="MarkdownV2"
            )
        except Exception as e:
            self.logger.error(f"Failed to read skill file: {e}")
            await update.message.reply_text(
                "Использование:\n"
                "/calendars — список календарей\n"
                "/calendars add <client_type> <url> [название] — добавить календарь\n"
                "/calendars info — инструкция для Яндекс.Календаря\n"
                "/calendars del <id> — удалить календарь\n"
                "/calendars edit <id> <field> <value> — изменить поле (name, url, client_type, timezone)\n"
                "/calendars event <id> <summary> — создать событие на сегодня\n"
                "/calendars event <id> <summary> | <start> — с указанием начала (ISO)\n"
                "/calendars event <id> <summary> | <start> | <end> — с началом и концом",
            )

    async def _send_info(self, update: Update):
        try:
            text = INFO_FILE.read_text(encoding="utf-8")
            await update.message.reply_text(
                md2tgmd.escape(text), parse_mode="MarkdownV2"
            )
        except Exception as e:
            self.logger.error(f"Failed to read info file: {e}")
            await update.message.reply_text(
                "Инструкция временно недоступна. Попробуйте позже."
            )

    async def _add_calendar(self, update: Update, args: list, chat_id: str):
        if len(args) < 2:
            await update.message.reply_text(
                "Использование: /calendars add <client_type> <url> [название]\n\n"
                "Пример: /calendars add caldav https://user@yandex.ru:пароль@caldav.yandex.ru/calendars/login/events-123/ Мой календарь\n\n"
                "Подробнее: /calendars info"
            )
            return

        client_type = args[0]
        url = args[1]
        name = " ".join(args[2:]) if len(args) > 2 else ""
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

    async def _list_calendars(self, update: Update, chat_id: str):
        calendars = self.ics_client.get_calendars(chat_id)
        if calendars is None:
            await update.message.reply_text("Ошибка при получении списка календарей.")
            return
        if not calendars:
            await update.message.reply_text("У вас нет добавленных календарей.")
            return

        lines = ["Ваши календари:"]
        for cal in calendars:
            cal_id = cal.get("id", "?")
            cal_name = cal.get("name") or "(без имени)"
            cal_type = cal.get("client_type", "?")
            cal_url = cal.get("url", "?")
            cal_tz = cal.get("timezone", "")
            tz_line = f"\n  Часовой пояс: {cal_tz}" if cal_tz else ""
            lines.append(
                f"• ID: `{cal_id}`\n  Имя: {cal_name}\n  Тип: {cal_type}"
                f"\n  URL: {cal_url}{tz_line}"
            )

        await update.message.reply_text("\n\n".join(lines), parse_mode="Markdown")

    async def _delete_calendar(self, update: Update, cal_id: str, chat_id: str):
        success = self.ics_client.delete_calendar(cal_id, chat_id)
        if success:
            await update.message.reply_text(
                f"Календарь `{cal_id}` удалён.", parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"Не удалось удалить календарь `{cal_id}`.", parse_mode="Markdown"
            )

    async def _edit_calendar(
        self, update: Update, cal_id: str, field: str, value: str, chat_id: str
    ):
        if field not in EDITABLE_FIELDS:
            await update.message.reply_text(
                f"Поле `{field}` нельзя редактировать. Допустимые: "
                + ", ".join(sorted(EDITABLE_FIELDS))
            )
            return
        if not value:
            await update.message.reply_text("Укажите новое значение для поля.")
            return

        success = self.ics_client.update_calendar(cal_id, chat_id, **{field: value})
        if success:
            await update.message.reply_text(
                f"Календарь `{cal_id}` обновлён: `{field}` → `{value}`",
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text(
                f"Не удалось обновить календарь `{cal_id}`.", parse_mode="Markdown"
            )

    async def _create_event(self, update: Update, cal_id: str, rest: str, chat_id: str):
        parts = [p.strip() for p in rest.split("|")]
        summary = parts[0]
        start_str = parts[1] if len(parts) > 1 else ""
        end_str = parts[2] if len(parts) > 2 else ""

        now = datetime.now(timezone.utc)
        if start_str:
            try:
                start = datetime.fromisoformat(start_str)
            except ValueError:
                await update.message.reply_text(
                    "Неверный формат даты. Используйте ISO: 2026-07-28T12:00:00+03:00"
                )
                return
        else:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        if end_str:
            try:
                end = datetime.fromisoformat(end_str)
            except ValueError:
                await update.message.reply_text("Неверный формат даты окончания.")
                return
        else:
            end = None

        payload = {
            "summary": summary,
            "description": "",
            "location": "",
            "start": start.isoformat(),
            "end": end.isoformat() if end else None,
            "all_day": not bool(start_str),
        }

        success = self.ics_client.create_event(cal_id, chat_id, **payload)
        if success:
            await update.message.reply_text(
                f"Событие «{summary}» создано в календаре `{cal_id}`.",
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text(
                f"Не удалось создать событие в календаре `{cal_id}`.",
                parse_mode="Markdown",
            )
