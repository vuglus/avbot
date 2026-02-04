from services.config_service import Config
import openai

class YandexGPClient:
    def __init__(self, config: Config):
        # Initialize OpenAI client for Yandex Cloud
        self.config = config
        self.client = openai.OpenAI(
            api_key=config.getYandex('key'),
            base_url="https://rest-assistant.api.cloud.yandex.net/v1",
            project=config.getCloudFolder(),
        )

    def request(self, prompt, tools=None):
        # Initial request to YandexGPT
        response = self.client.responses.create(
            model=f"gpt://{self.config.getCloudFolder()}/{self.config.getYandex('model')}",
            instructions=self.config.getYandex('system_prompt'),
            tools=tools if tools else None,
            input=prompt,
        )

        return response
