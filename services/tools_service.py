import logging
import json
import requests
from yandex_ai_studio_sdk import AIStudio
from services.dialog_service import DialogService
from storage.file_storage import FileDialogStorage, DEFAULT_TOPIC
from services.config_service import Config
from services.yandex_index_service import YandexIndexService
from clients.icsclient import ICSClient

# Initialize logger
logger = logging.getLogger(__name__)


class ToolService:
    def __init__(self, config: Config):
        self.config = config
        self.ics = ICSClient(config)

    def call_tool(self, tool_name: str, args: dict, user_id: int = None) -> dict:
        """Route tool calls to appropriate handler."""
        if tool_name in ("add_calendar_event", "list_calendars"):
            return self._call_calendar_tool(tool_name, args, user_id)
        return self.call_mcp_tool(tool_name, args)

    def _call_calendar_tool(
        self, tool_name: str, args: dict, user_id: int = None
    ) -> dict:
        """Handle calendar-related tool calls."""
        try:
            if tool_name == "list_calendars":
                calendars = self.ics.get_calendars(str(user_id))
                all_calendars = calendars or []
                writable = [
                    c
                    for c in all_calendars
                    if not any(
                        tag in (c.get("name", "") or "")
                        for tag in ("Google", "RO", "ICS")
                    )
                ]
                result = {"calendars": writable}
                if all_calendars and len(writable) < len(all_calendars):
                    result["skipped_readonly"] = len(all_calendars) - len(writable)
                if len(writable) == 1:
                    result["note"] = (
                        "У вас один доступный для записи календарь. Используйте его calendar_id "
                        "для создания события, не спрашивая пользователя."
                    )
                elif len(writable) == 0:
                    result["note"] = "У вас нет календарей, доступных для записи."
                return result

            if tool_name == "add_calendar_event":
                calendar_id = args.get("calendar_id")
                if not calendar_id:
                    return {"error": "calendar_id is required"}
                success = self.ics.create_event(
                    calendar_id,
                    str(user_id),
                    summary=args.get("summary", ""),
                    description=args.get("description", ""),
                    location=args.get("location", ""),
                    start=args.get("start", ""),
                    end=args.get("end", ""),
                    all_day=args.get("all_day", False),
                )
                if success:
                    return {"status": "ok", "message": "Событие создано"}
                return {"error": "Не удалось создать событие"}

            return {"error": f"Unknown calendar tool: {tool_name}"}
        except Exception as e:
            logger.error(f"Calendar tool error: {e}")
            return {"error": str(e)}

    def call_mcp_tool(self, tool_name: str, args: dict) -> dict:
        """
        Call MCP tool via SSE JSON-RPC.
        tool_name: "scoring_post" or "briefReport_post"
        args: dict of tool parameters, e.g. {"query_inn": "7733215614"}
        """
        try:
            logger.info(f"Calling MCP tool via SSE: {tool_name} with args: {args}")

            # Prepare JSON-RPC payload
            payload = {"jsonrpc": "2.0", "method": tool_name, "params": args, "id": 1}

            # SSE expects GET with headers for key
            headers = {
                "Content-Type": "application/json",
            }

            # SSE через requests + sseclient
            with requests.get(
                self.config.get("mcp", "b2b_inn_check_url"),
                headers=headers,
                stream=True,
            ) as response:
                client = sseclient.SSEClient(response)

                # Отправляем команду (через POST к /sse, иногда нужно в SSE подключении писать JSON-RPC, зависит от MCP)
                # Здесь MCP обычно ждёт события типа 'message' с JSON payload
                # Но в публичном SDK это скрыто, поэтому ниже пример "прослушки" ответа
                for event in client.events():
                    try:
                        data = json.loads(event.data)
                        # Ищем ответ с нужным id
                        if data.get("id") == 1:
                            logger.info(
                                f"MCP tool {tool_name} returned: {data.get('result')}"
                            )
                            return data.get("result")
                    except json.JSONDecodeError:
                        continue

            return {"error": "No response from MCP tool"}

        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {str(e)}")
            return {"error": str(e)}

    def _prepare_tools(self, index_keys: list):
        """Prepare tools for YandexGPT request"""
        # Start with the base tools
        tools = []

        # Add file search tools if we have index keys
        if index_keys:
            # Filter out any None or empty values
            valid_index_keys = [key for key in index_keys if key]
            if valid_index_keys:
                tools.append(
                    {
                        "type": "file_search",
                        "vector_store_ids": valid_index_keys,
                    }
                )

        # Add web search tool
        tools.append(
            {
                "type": "web_search",
                "filters": {"allowed_domains": []},
                "search_context_size": "medium",
            }
        )

        # Add calendar tools
        tools.extend(
            [
                {
                    "type": "function",
                    "name": "list_calendars",
                    "description": "Показать список календарей пользователя",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
                {
                    "type": "function",
                    "name": "add_calendar_event",
                    "description": "Создать событие в календаре",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "calendar_id": {
                                "type": "string",
                                "description": "ID календаря из list_calendars",
                            },
                            "summary": {
                                "type": "string",
                                "description": "Название события",
                            },
                            "description": {
                                "type": "string",
                                "description": "Описание события",
                            },
                            "location": {
                                "type": "string",
                                "description": "Место или ссылка",
                            },
                            "start": {
                                "type": "string",
                                "description": "Начало в ISO формате, например 2026-07-28T15:00:00+03:00",
                            },
                            "end": {
                                "type": "string",
                                "description": "Конец в ISO формате",
                            },
                            "all_day": {
                                "type": "boolean",
                                "description": "Событие на весь день",
                            },
                        },
                        "required": ["calendar_id", "summary"],
                    },
                },
            ]
        )

        # # Add MCP tools
        # tools.extend([
        #     {
        #         "type": "function",
        #         "function": {
        #             "name": "scoring_post",
        #             "description": "Скоринг организации по ИНН",
        #             "parameters": {
        #                 "type": "object",
        #                 "properties": {
        #                     "query_inn": {
        #                         "type": "string",
        #                         "description": "ИНН организации (можно указать до 100 ИНН-ов через запятую). Обязательный, если не указан ОГРН"
        #                     }
        #                 },
        #                 "required": ["query_inn"]
        #             }
        #         }
        #     },
        #     {
        #         "type": "function",
        #         "function": {
        #             "name": "briefReport_post",
        #             "description": "Краткий отчет по организации",
        #             "parameters": {
        #                 "type": "object",
        #                 "properties": {
        #                     "query_inn": {"type": "string"}
        #                 },
        #                 "required": ["query_inn"]
        #             },
        #             "strict": True
        #         }
        #     }
        # ])

        return tools

    def _get_user_index_id(self, user_id: int):
        """Get combined index IDs for a specific user.

        Args:
            user_id: User ID to get index IDs for

        Returns:
            List of unique index IDs preserving order
        """
        storage = FileDialogStorage()
        dialogs_service = DialogService(storage)
        # Получаем текущий топик пользователя
        dialog_data = storage.load_dialog(user_id)
        current_topic = dialog_data.get("current_topic", DEFAULT_TOPIC)
        logger.info(f"Current topic: {current_topic}")

        # Get index ID for user's default topic
        index_def = self.config.getYandex("index")
        index_id = self.config.getYandex("user_index").get(str(user_id), index_def)

        try:
            sdk = AIStudio(
                folder_id=self.config.getCloudFolder(), auth=self.config.getCloudKey()
            )
            index_service = YandexIndexService(
                sdk, self.config.getCloudFolder(), dialogs_service
            )
            index_id = (
                index_service.get_index_id_for_topic(user_id, current_topic) or index_id
            )

        except Exception as e:
            logger.error(f"Error getting index IDs for user {user_id}: {e}")
            pass

        # Remove duplicates while preserving order using dict (Python 3.7+ maintains insertion order)
        # Filter out None/empty values during deduplication

        return index_id
