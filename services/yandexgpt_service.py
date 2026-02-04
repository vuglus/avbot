import logging
import json
from services.tools_service import ToolService
from clients.yandexgpt import YandexGPClient
from services.config_service import Config

class YandexGPTService:
    def __init__(self, config: Config):
        self.config = config
        self.client = YandexGPClient(config)
        self.tools =  ToolService(config)
        # Initialize logger
        self.logger = logging.getLogger(__name__)

    def _make_yandexgpt_request(self, prompt: str, tools=None) -> str:
        """Make a request to YandexGPT through OpenAI library"""
        try:
            self.logger.info(f"Making YandexGPT request with prompt: {prompt}")
            
            # Initial request to YandexGPT
            response = self.client.request(prompt, tools)

            if response.status != 'completed':
                self.logger.error(f"Error calling YandexGPT: {response!r}")
                return f"Ошибка при обращении к YandexGPT: {response.error.message}"
            
            self.logger.info(f"Success: {response!r}.")

            # 1. Ищем tool_call в response.output
            tool_calls = [
                item for item in response.output
                if item.type == "function_call"
            ]

            if tool_calls:
                # 2. Берем первый tool_call
                tool_call = tool_calls[0]
                tool_name = tool_call.name          # атрибут name
                args = json.loads(tool_call.arguments)  # arguments хранится как JSON строка

                self.logger.info(f"Model wants to call tool: {tool_name} with args: {args}")

                # 3. Вызываем MCP
                tool_result = self.tools.call_mcp_tool(tool_name, args)

                # 4. Отдаем результат обратно модели
                
                final_response = self.client.request([
                    {"role": "user", "content": prompt},
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,  # ВАЖНО: id, не name
                        "content": json.dumps(tool_result, ensure_ascii=False),
                    },
                ])

                return final_response.output_text
            else:
                # 5. Tool не нужен — обычный ответ
                return response.output_text
        except Exception as e:
            self.logger.error(f"Error calling YandexGPT: {str(e)}")
            return f"Ошибка при обращении к YandexGPT: {str(e)}"

    def ask_yandexgpt(self, prompt: str, user_id: int) -> str:
        """Request to YandexGPT through OpenAI library"""
        # Get index IDs for the user
        index_id = self.tools._get_user_index_id(user_id)
        
        tools = self.tools._prepare_tools([index_id])
        return self._make_yandexgpt_request(prompt, tools)

    def ask_yandexgpt_with_context(self, prompt: str, dialog_context: list, user_id: int) -> str:
        """Request to YandexGPT with dialog context through OpenAI library"""
        try:
            # For the chat.completions.create API, we need to pass the context as messages
            messages = []
            # Add dialog history
            for msg in dialog_context:
                role = msg.get("role", "user")
                text = msg.get("text", "") if "text" in msg else msg.get("content", "")
                messages.append({"role": role, "content": text})
            
            # Add the new user prompt
            messages.append({"role": "user", "content": prompt})
            # Get index IDs for the user
            index_id = self.tools._get_user_index_id(user_id)
            # Prepare tools
            tools = self.tools._prepare_tools([index_id])
            self.logger.info(f"Making YandexGPT request with context: {messages}, tools: {tools}")
            
            # Make the request to Yandex Cloud through OpenAI library
            response = self._make_yandexgpt_request(prompt, tools)
            
            return response
        except Exception as e:
            self.logger.error(f"Error calling YandexGPT with context: {e!r}")
            return f"Ошибка при обращении к YandexGPT: {e!r}"