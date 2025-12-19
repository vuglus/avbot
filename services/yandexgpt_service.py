import logging
import json
from services.tools_service import _prepare_tools, call_mcp_tool, _get_user_index_id
from clients.yandexgpt import YandexGPClient

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize OpenAI client for Yandex Cloud
client = YandexGPClient()

def _make_yandexgpt_request(prompt: str, tools=None) -> str:
    """Make a request to YandexGPT through OpenAI library"""
    try:
        logger.info(f"Making YandexGPT request with prompt: {prompt}")
        
        # Initial request to YandexGPT
        response = client.request(prompt, tools)

        if response.status != 'completed':
            logger.error(f"Error calling YandexGPT: {response!r}")
            return f"Ошибка при обращении к YandexGPT: {response.error.message}"
        
        logger.info(f"Success: {response!r}.")

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

            logger.info(f"Model wants to call tool: {tool_name} with args: {args}")

            # 3. Вызываем MCP
            tool_result = call_mcp_tool(tool_name, args)

            # 4. Отдаем результат обратно модели
            
            final_response = client.request([
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
        logger.error(f"Error calling YandexGPT: {str(e)}")
        return f"Ошибка при обращении к YandexGPT: {str(e)}"

def ask_yandexgpt(prompt: str, user_id: int) -> str:
    """Request to YandexGPT through OpenAI library"""
    # Get index IDs for the user
    index_id = _get_user_index_id(user_id)
    
    tools = _prepare_tools([index_id])
    return _make_yandexgpt_request(prompt, tools)

def ask_yandexgpt_with_context(prompt: str, dialog_context: list, user_id: int) -> str:
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
        index_id = _get_user_index_id(user_id)
        # Prepare tools
        tools = _prepare_tools([index_id])
        logger.info(f"Making YandexGPT request with context: {messages}, tools: {tools}")
        
        # Make the request to Yandex Cloud through OpenAI library
        response = _make_yandexgpt_request(prompt, tools)
        
        return response
    except Exception as e:
        logger.error(f"Error calling YandexGPT with context: {e!r}")
        return f"Ошибка при обращении к YandexGPT: {e!r}"