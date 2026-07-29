import logging
import json
from services.tools_service import ToolService
from clients.yandexgpt import YandexGPClient, YandexGPTError
from services.config_service import Config


class YandexGPTService:
    def __init__(self, config: Config):
        self.config = config
        self.client = YandexGPClient(config)
        self.tools = ToolService(config)
        self.logger = logging.getLogger(__name__)

    def _make_yandexgpt_request(
        self, prompt: str, tools=None, user_id: int = None, messages: list = None
    ) -> str:
        try:
            self.logger.info(f"Making YandexGPT request with prompt: {prompt}")

            if messages is None:
                messages = [{"role": "user", "content": prompt}]

            for _ in range(5):
                response = self.client.request(messages, tools)
                self.logger.info(f"Success: {response!r}.")

                tool_calls = [
                    item for item in response.output if item.type == "function_call"
                ]
                if not tool_calls:
                    return response.output_text or ""

                tool_call = tool_calls[0]
                tool_name = tool_call.name
                args = json.loads(tool_call.arguments)

                self.logger.info(
                    f"Model wants to call tool: {tool_name} with args: {args}"
                )

                tool_result = self.tools.call_tool(tool_name, args, user_id=user_id)

                for item in response.output:
                    if item.type == "function_call":
                        messages.append(item.model_dump())
                messages.append(
                    {
                        "type": "function_call_output",
                        "call_id": tool_call.call_id,
                        "output": json.dumps(tool_result, ensure_ascii=False),
                    }
                )

            return response.output_text or "Готово."
        except Exception as e:
            self.logger.error(f"Error calling YandexGPT: {str(e)}")
            return f"Ошибка при обращении к YandexGPT: {str(e)}"

    def ask_yandexgpt(self, prompt: str, user_id: int) -> str:
        index_id = self.tools._get_user_index_id(user_id)
        tools = self.tools._prepare_tools([index_id])
        return self._make_yandexgpt_request(prompt, tools, user_id=user_id)

    def ask_yandexgpt_with_context(
        self, prompt: str, dialog_context: list, user_id: int
    ) -> str:
        messages = []
        for msg in dialog_context:
            role = msg.get("role", "user")
            text = msg.get("text", "") if "text" in msg else msg.get("content", "")
            messages.append({"role": role, "content": text})
        messages.append({"role": "user", "content": prompt})
        index_id = self.tools._get_user_index_id(user_id)
        tools = self.tools._prepare_tools([index_id])
        self.logger.info(
            f"Making YandexGPT request with context: {messages}, tools: {tools}"
        )
        response = self._make_yandexgpt_request(
            prompt, tools, user_id=user_id, messages=messages
        )
        return response
