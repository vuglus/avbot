import logging
import asyncio
from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel, Field
from typing import Annotated, Optional
from telegram import Bot
import uvicorn
from services.config_service import Config
from services.yandexgpt_service import YandexGPTService


# ──────────────────────────────────────────────
# Response models
# ──────────────────────────────────────────────
class SuccessResponse(BaseModel):
    status: str
    message_id: Optional[int] = None


class ErrorResponse(BaseModel):
    error: dict


# ──────────────────────────────────────────────
# Request models
# ──────────────────────────────────────────────
class SendMessageRequest(BaseModel):
    """Send a text message to a Telegram chat."""

    chat_id: int = Field(..., description="Telegram chat ID (user or group)")
    text: str = Field(..., description="Message text (supports MarkdownV2 or HTML)")
    parse_mode: Optional[str] = Field(
        None, description="Parse mode: MarkdownV2, HTML, or None"
    )
    disable_web_page_preview: Optional[bool] = Field(
        False, description="Disable link previews"
    )
    disable_notification: Optional[bool] = Field(False, description="Send silently")
    reply_to_message_id: Optional[int] = Field(
        None, description="Reply to a specific message"
    )


class SendPhotoRequest(BaseModel):
    """Send a photo to a Telegram chat."""

    chat_id: int = Field(..., description="Telegram chat ID")
    photo: str = Field(..., description="URL or file_id of the photo")
    caption: Optional[str] = Field(None, description="Photo caption")
    parse_mode: Optional[str] = Field(None, description="Parse mode for caption")


class SendDocumentRequest(BaseModel):
    """Send a document to a Telegram chat."""

    chat_id: int = Field(..., description="Telegram chat ID")
    document: str = Field(..., description="URL or file_id of the document")
    caption: Optional[str] = Field(None, description="Document caption")
    filename: Optional[str] = Field(None, description="Display filename")


class SendActionRequest(BaseModel):
    """Send a chat action (typing, upload_photo, etc.)."""

    chat_id: int = Field(..., description="Telegram chat ID")
    action: str = Field(
        ...,
        description="Chat action: typing, upload_photo, record_video, "
        "upload_video, record_voice, upload_voice, "
        "upload_document, find_location, record_video_note, "
        "upload_video_note",
    )


class ForwardMessageRequest(BaseModel):
    """Forward a message from one chat to another."""

    chat_id: int = Field(..., description="Target Telegram chat ID")
    from_chat_id: int = Field(..., description="Source chat ID")
    message_id: int = Field(..., description="Message ID to forward")


class CalendarEventRequest(BaseModel):
    """Calendar event from ICS service webhook."""

    chat_id: int = Field(..., description="Telegram chat ID to notify")
    summary: str = Field("", description="Event title/summary")
    description: str = Field("", description="Event description")
    location: str = Field("", description="Event location")
    start: str = Field("", description="Start datetime (ISO format)")
    end: str = Field("", description="End datetime (ISO format)")
    all_day: bool = Field(False, description="All-day event flag")
    calendar_id: str = Field("", description="Calendar ID")
    calendar_url: str = Field("", description="Calendar URL")
    calendar_name: str = Field("", description="Calendar name")
    uid: str = Field("", description="Event UID")


# ──────────────────────────────────────────────
# API Server
# ──────────────────────────────────────────────
class ApiServer:
    """
    HTTP API server that wraps the Telegram bot.

    Allows external services to send messages to Telegram chats
    via REST API calls authenticated with an API key.
    """

    def __init__(
        self,
        api_key: str,
        bot: Bot,
        port: int,
        config: Config,
        host: str = "0.0.0.0",
        logger: logging.Logger = None,
    ):
        self.api_key = api_key
        self.bot = bot
        self.port = port
        self.host = host
        self.config = config
        self.gpt = YandexGPTService(config)
        self.app = FastAPI(
            title="AVBot Telegram API",
            description="API for sending messages to Telegram via AVBot",
            version="1.0.0",
        )
        self.logger = logger or logging.getLogger(__name__)
        self._register_routes()

    # ── Authentication dependency ──────────────────
    async def _authenticate(
        self,
        x_api_key: Annotated[str | None, Header(alias="x-api-key")] = None,
    ) -> None:
        """Dependency for x-api-key authentication."""
        if not x_api_key or x_api_key != self.api_key:
            raise HTTPException(
                status_code=401,
                detail={"code": 401, "message": "Unauthorized"},
            )

    # ── Route registration ─────────────────────────
    def _register_routes(self):
        @self.app.get("/health", response_model=SuccessResponse)
        async def health():
            """Health check endpoint."""
            return {"status": "ok"}

        @self.app.post(
            "/send",
            response_model=SuccessResponse,
            responses={401: {"model": ErrorResponse}},
        )
        async def send_message(
            req: SendMessageRequest,
            _: Annotated[None, Depends(self._authenticate)],
        ):
            """Send a text message to a Telegram chat."""
            self.logger.info(
                "Sending message to chat %s: %s...",
                req.chat_id,
                req.text[:50] if req.text else "",
            )
            try:
                msg = await self.bot.send_message(
                    chat_id=req.chat_id,
                    text=req.text,
                    parse_mode=req.parse_mode,
                    disable_web_page_preview=req.disable_web_page_preview,
                    disable_notification=req.disable_notification,
                    reply_to_message_id=req.reply_to_message_id,
                )
                return {"status": "sent", "message_id": msg.message_id}
            except Exception as e:
                self.logger.error("Failed to send message: %s", e)
                raise HTTPException(
                    status_code=500,
                    detail={"code": 500, "message": str(e)},
                )

        @self.app.post(
            "/sendPhoto",
            response_model=SuccessResponse,
            responses={401: {"model": ErrorResponse}},
        )
        async def send_photo(
            req: SendPhotoRequest,
            _: Annotated[None, Depends(self._authenticate)],
        ):
            """Send a photo to a Telegram chat."""
            self.logger.info("Sending photo to chat %s", req.chat_id)
            try:
                msg = await self.bot.send_photo(
                    chat_id=req.chat_id,
                    photo=req.photo,
                    caption=req.caption,
                    parse_mode=req.parse_mode,
                )
                return {"status": "sent", "message_id": msg.message_id}
            except Exception as e:
                self.logger.error("Failed to send photo: %s", e)
                raise HTTPException(
                    status_code=500,
                    detail={"code": 500, "message": str(e)},
                )

        @self.app.post(
            "/sendDocument",
            response_model=SuccessResponse,
            responses={401: {"model": ErrorResponse}},
        )
        async def send_document(
            req: SendDocumentRequest,
            _: Annotated[None, Depends(self._authenticate)],
        ):
            """Send a document to a Telegram chat."""
            self.logger.info("Sending document to chat %s", req.chat_id)
            try:
                msg = await self.bot.send_document(
                    chat_id=req.chat_id,
                    document=req.document,
                    caption=req.caption,
                    filename=req.filename,
                )
                return {"status": "sent", "message_id": msg.message_id}
            except Exception as e:
                self.logger.error("Failed to send document: %s", e)
                raise HTTPException(
                    status_code=500,
                    detail={"code": 500, "message": str(e)},
                )

        @self.app.post(
            "/sendAction",
            response_model=SuccessResponse,
            responses={401: {"model": ErrorResponse}},
        )
        async def send_action(
            req: SendActionRequest,
            _: Annotated[None, Depends(self._authenticate)],
        ):
            """Send a chat action (typing, upload_photo, etc.)."""
            self.logger.info("Sending action '%s' to chat %s", req.action, req.chat_id)
            try:
                await self.bot.send_chat_action(
                    chat_id=req.chat_id,
                    action=req.action,
                )
                return {"status": "sent"}
            except Exception as e:
                self.logger.error("Failed to send action: %s", e)
                raise HTTPException(
                    status_code=500,
                    detail={"code": 500, "message": str(e)},
                )

        @self.app.post(
            "/forwardMessage",
            response_model=SuccessResponse,
            responses={401: {"model": ErrorResponse}},
        )
        async def forward_message(
            req: ForwardMessageRequest,
            _: Annotated[None, Depends(self._authenticate)],
        ):
            """Forward a message from one chat to another."""
            self.logger.info(
                "Forwarding message %s from chat %s to chat %s",
                req.message_id,
                req.from_chat_id,
                req.chat_id,
            )
            try:
                msg = await self.bot.forward_message(
                    chat_id=req.chat_id,
                    from_chat_id=req.from_chat_id,
                    message_id=req.message_id,
                )
                return {"status": "sent", "message_id": msg.message_id}
            except Exception as e:
                self.logger.error("Failed to forward message: %s", e)
                raise HTTPException(
                    status_code=500,
                    detail={"code": 500, "message": str(e)},
                )

        @self.app.post(
            "/calendar/event",
            response_model=SuccessResponse,
            responses={401: {"model": ErrorResponse}},
        )
        async def calendar_event(
            req: CalendarEventRequest,
            _: Annotated[None, Depends(self._authenticate)],
        ):
            """Receive calendar events, summarize via LLM, and send to Telegram."""
            self.logger.info("Received calendar event: summary=%s", req.summary)

            system_prompt = self.config.get(
                "ics",
                "system_prompt",
                "Ты — ассистент, который кратко summarises события календаря.",
            )

            prompt = (
                f"{system_prompt}\n\n"
                f"Событие календаря:\n"
                f"Название: {req.summary or ''}\n"
                f"Описание: {req.description or ''}\n"
                f"Начало: {req.start or ''}\n"
                f"Конец: {req.end or ''}\n"
                f"Место: {req.location or ''}\n"
                f"Календарь: {req.calendar_name or req.calendar_url or ''}\n"
            )

            try:
                response = await asyncio.to_thread(
                    self.gpt.ask_yandexgpt, prompt, req.chat_id
                )
                await self.bot.send_message(chat_id=req.chat_id, text=response)
                self.logger.info(
                    "Sent calendar event notification to chat %s", req.chat_id
                )
                return {"status": "sent"}
            except Exception as e:
                self.logger.error(
                    "Failed to process calendar event for chat %s: %s", req.chat_id, e
                )
                raise HTTPException(
                    status_code=500,
                    detail={"code": 500, "message": str(e)},
                )

    # ── Lifecycle ──────────────────────────────────
    async def run(self):
        """Start the uvicorn server."""
        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info",
        )
        server = uvicorn.Server(config)
        await server.serve()

    def getTask(self):
        """Return the run coroutine for use with asyncio.create_task."""
        return self.run()
