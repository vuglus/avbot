import logging
import json
import requests
from clients.mcp import MCPClient
from services.config_service import MCP_B2B_INN_CHECK_URL, INDEX_KEYS

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


def _prepare_tools(index_keys):
    """Prepare tools for YandexGPT request"""
    # Start with the base tools
    tools = []
    
    # Add file search tools if we have index keys
    if index_keys:
        tools.append({
            "type": "file_search",
            "vector_store_ids": index_keys,
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

# Make functions available for import
__all__ = ['_prepare_tools', 'call_mcp_tool']
