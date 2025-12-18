from services.config_service import BOT_KEY, YCLOUD_FOLDER_ID, SYSTEM_PROMPT, SYSTEM_MODEL, INDEX_KEYS
import openai

class YandexGPClient:
    def __init__(self):
        # Initialize OpenAI client for Yandex Cloud
        self.client = openai.OpenAI(
            api_key=BOT_KEY,
            base_url="https://rest-assistant.api.cloud.yandex.net/v1",
            project=YCLOUD_FOLDER_ID,
        )

    def request(self, prompt, tools=None):
        # Initial request to YandexGPT
        response = self.client.responses.create(
            model=f"gpt://{YCLOUD_FOLDER_ID}/{SYSTEM_MODEL}",
            instructions=SYSTEM_PROMPT,
            tools=tools if tools else None,
            input=prompt,
        )

        return response
