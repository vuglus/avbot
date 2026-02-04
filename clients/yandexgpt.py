from services.config_service import config, BOT_KEY, SYSTEM_PROMPT, SYSTEM_MODEL
import openai

class YandexGPClient:
    def __init__(self):
        # Initialize OpenAI client for Yandex Cloud
        self.client = openai.OpenAI(
            api_key=BOT_KEY,
            base_url="https://rest-assistant.api.cloud.yandex.net/v1",
            project=config.getCloudFolder(),
        )

    def request(self, prompt, tools=None):
        # Initial request to YandexGPT
        response = self.client.responses.create(
            model=f"gpt://{config.getCloudFolder()}/{SYSTEM_MODEL}",
            instructions=SYSTEM_PROMPT,
            tools=tools if tools else None,
            input=prompt,
        )

        return response
