from services.config_service import Config
import openai
from openai.types.responses import Response

class YandexGPTError(Exception):
    pass


class YandexGPTApiError(YandexGPTError):
    pass


class YandexGPTIncompleteError(YandexGPTError):
    def __init__(self, reason: str):
        super().__init__(f"Incomplete response from YandexGPT (reason={reason})")
        self.reason = reason

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
        self._validate_response(response)

        return response
    
    def _validate_response(self, response: Response) -> None:
        # 1. Успешный кейс
        if response.status == "completed":
            if not response.output_text:
                raise YandexGPTError(
                    "Completed response without output_text (contract violation)"
                )
            return

        # 2. Ошибка API
        if response.error is not None:
            raise YandexGPTApiError(response.error.message)

        # 3. Incomplete (content_filter и т.п.)
        if response.status == "incomplete":
            reason = (
                response.incomplete_details.reason
                if response.incomplete_details
                else "unknown"
            )
            raise YandexGPTIncompleteError(reason)

        # 4. Неизвестное состояние
        raise YandexGPTError(f"Unknown response status: {response.status}")
