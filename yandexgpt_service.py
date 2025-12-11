import logging
from yandex_cloud_ml_sdk import YCloudML
from config import YCLOUD_API_KEY, YCLOUD_FOLDER_ID, SYSTEM_PROMPT

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize YCloudML
sdk = YCloudML(folder_id=YCLOUD_FOLDER_ID, auth=YCLOUD_API_KEY)
model = sdk.models.completions("yandexgpt", model_version="rc").configure(temperature=0.3)


def ask_yandexgpt(prompt: str) -> str:
    """Request to YandexGPT through YCloudML"""
    try:
        result = model.run([
            {"role": "system", "text": SYSTEM_PROMPT},
            {"role": "user", "text": prompt}
        ])
        
        if result and result.alternatives:
            return result.alternatives[0].text
        else:
            return "Ответ от YandexGPT пустой или в неожиданном формате."
    except Exception as e:
        logger.error(f"Error calling YandexGPT: {str(e)}")
        return f"Ошибка при обращении к YandexGPT: {str(e)}"