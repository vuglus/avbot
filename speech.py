import requests
import os


def recognize_speech(filepath: str, api_key: str, folder_id: str, lang: str = 'ru-RU') -> str:
    with open(filepath, 'rb') as f:
        audio_data = f.read()

    headers = {
        'Authorization': f'Api-Key {api_key}',
        'Content-Type': 'audio/x-wav'
    }

    params = {
        'folderId': folder_id,
        'lang': lang
    }

    response = requests.post(
        'https://stt.api.cloud.yandex.net/speech/v1/stt:recognize',
        headers=headers,
        params=params,
        data=audio_data
    )

    if response.status_code == 200:
        return response.json().get('result', '')
    else:
        raise RuntimeError(f"SpeechKit error: {response.status_code}, {response.text}")