import logging
import openai
from json import dumps
from services.config_service import BOT_KEY, YCLOUD_FOLDER_ID, SYSTEM_PROMPT, SYSTEM_MODEL, INDEX_KEYS

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize OpenAI client for Yandex Cloud
client = openai.OpenAI(
    api_key=BOT_KEY,
    base_url="https://rest-assistant.api.cloud.yandex.net/v1",
    project=YCLOUD_FOLDER_ID,
)

def _prepare_tools():
    """Prepare tools for YandexGPT request"""
    tools = []
    if INDEX_KEYS:
        tools.append({
            "type": "file_search",
            "vector_store_ids": INDEX_KEYS,
        })
    return tools

def _make_yandexgpt_request(prompt: str, tools=None) -> str:
    """Make a request to YandexGPT through OpenAI library"""
    try:
        response = client.responses.create(
            model=f"gpt://{YCLOUD_FOLDER_ID}/{SYSTEM_MODEL}",
            instructions=SYSTEM_PROMPT,
            tools=tools if tools else None,
            input=prompt,
        )
        
        return response.output_text
    except Exception as e:
        logger.error(f"Error calling YandexGPT: {str(e)}")
        return f"Ошибка при обращении к YandexGPT: {str(e)}"

def ask_yandexgpt(prompt: str) -> str:
    """Request to YandexGPT through OpenAI library"""
    tools = _prepare_tools()
    return _make_yandexgpt_request(prompt, tools)

def ask_yandexgpt_with_context(prompt: str, dialog_context: list) -> str:
    """Request to YandexGPT with dialog context through OpenAI library"""
    try:
        # For the responses.create API, we need to pass the context differently
        # Build the full context including system prompt and dialog history
        # Convert dialog context to a single string prompt with context
        context_parts = []
        
        # Add dialog history
        for msg in dialog_context:
            role = msg.get("role", "user")
            text = msg.get("text", "") if "text" in msg else msg.get("content", "")
            context_parts.append(f"{role}: {text}")
        
        # Combine all context with the new prompt
        full_prompt = "\n".join(context_parts) + f"\nuser: {prompt}" if context_parts else prompt
        
        # Prepare tools if we have index keys
        tools = _prepare_tools()
        logger.error(f"full_prompt: {full_prompt}")
        
        # Make the request to Yandex Cloud through OpenAI library
        response = _make_yandexgpt_request(full_prompt, tools)
        
        return response
    except Exception as e:
        logger.error(f"Error calling YandexGPT with context: {str(e)}: {full_prompt}")
        return f"Ошибка при обращении к YandexGPT: {str(e)}: {full_prompt}"