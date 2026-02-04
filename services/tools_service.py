import logging
import json
import requests
from yandex_cloud_ml_sdk import YCloudML
from services.config_service import MCP_B2B_INN_CHECK_URL, INDEX_KEY, USER_INDEX_KEY
from services.dialog_service import load_user_dialog, DEFAULT_TOPIC
from services.config_service import config
from services.yandex_index_service import YandexIndexService

# Initialize logger
logger = logging.getLogger(__name__)


def call_mcp_tool(tool_name: str, args: dict) -> dict:
    """
    Call MCP tool via SSE JSON-RPC.
    tool_name: "scoring_post" or "briefReport_post"
    args: dict of tool parameters, e.g. {"query_inn": "7733215614"}
    """
    try:
        logger.info(f"Calling MCP tool via SSE: {tool_name} with args: {args}")

        # Prepare JSON-RPC payload
        payload = {
            "jsonrpc": "2.0",
            "method": tool_name,
            "params": args,
            "id": 1
        }

        # SSE expects GET with headers for key
        headers = {
            "Content-Type": "application/json",
        }

        # SSE через requests + sseclient
        with requests.get(MCP_B2B_INN_CHECK_URL, headers=headers, stream=True) as response:
            client = sseclient.SSEClient(response)

            # Отправляем команду (через POST к /sse, иногда нужно в SSE подключении писать JSON-RPC, зависит от MCP)
            # Здесь MCP обычно ждёт события типа 'message' с JSON payload
            # Но в публичном SDK это скрыто, поэтому ниже пример "прослушки" ответа
            for event in client.events():
                try:
                    data = json.loads(event.data)
                    # Ищем ответ с нужным id
                    if data.get("id") == 1:
                        logger.info(f"MCP tool {tool_name} returned: {data.get('result')}")
                        return data.get("result")
                except json.JSONDecodeError:
                    continue

        return {"error": "No response from MCP tool"}

    except Exception as e:
        logger.error(f"Error calling MCP tool {tool_name}: {str(e)}")
        return {"error": str(e)}


def _prepare_tools(index_keys: list):
    """Prepare tools for YandexGPT request"""
    # Start with the base tools
    tools = []
    
    # Add file search tools if we have index keys
    if index_keys:
        # Filter out any None or empty values
        valid_index_keys = [key for key in index_keys if key]
        if valid_index_keys:
            tools.append({
                "type": "file_search",
                "vector_store_ids": valid_index_keys,
            })
    
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

def _get_user_index_id(user_id: int) :
    """Get combined index IDs for a specific user.
    
    Args:
        user_id: User ID to get index IDs for
        
    Returns:
        List of unique index IDs preserving order
    """
    dialog_data = load_user_dialog(user_id)
    current_topic = dialog_data.get("current_topic", DEFAULT_TOPIC)
    logger.info(f"Current topic: {current_topic}")

    # Get index ID for user's default topic
    index_id = USER_INDEX_KEY.get(str(user_id), INDEX_KEY)

    try:
        sdk = YCloudML(folder_id=config.getCloudFolder(), auth=config.getCloudKey())
        index_service = YandexIndexService(sdk, config.getCloudFolder())
        index_id = index_service.get_index_id_for_topic(user_id, current_topic) or index_id

    except Exception as e:
        logger.error(f"Error getting index IDs for user {user_id}: {e}")
        pass
    
    # Remove duplicates while preserving order using dict (Python 3.7+ maintains insertion order)
    # Filter out None/empty values during deduplication
    
    return index_id

__all__ = ['_prepare_tools', 'call_mcp_tool', '_get_user_index_id']
