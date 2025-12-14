import yaml
import os

# Load configuration from YAML file
def load_config():
    with open('config.yml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# Load the configuration
config = load_config()

# Bot configuration
BOT_TOKEN = config['bot']['token']
BOT_WHITELIST = config['bot'].get('whitelist', [])

# Parse whitelist into a set of integers
if BOT_WHITELIST:
    WHITELIST = {int(uid) for uid in BOT_WHITELIST if str(uid).isdigit()}
else:
    WHITELIST = set()

# Yandex Cloud configuration
YCLOUD_API_KEY = config['ycloud']['api_key']
YCLOUD_FOLDER_ID = config['ycloud']['folder_id']
SYSTEM_PROMPT = config['yandex']['system_prompt']
SPEECH_API_KEY = config['yandex']['speech_api_key']
SYSTEM_MODEL = config['yandex']['model']
INDEX_KEYS = config['yandex'].get('index', [])
BOT_KEY = config['yandex']['key']

# S3 configuration
S3_ACCESS_KEY = config['s3']['access_key']
S3_SECRET_KEY = config['s3']['secret_key']
S3_BUCKET_NAME = config['s3']['bucket_name']