import yaml

# Load configuration from YAML file
def load_config():
    with open('config.yml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

class Config:
    def __init__(self, config):
        self.config = config
    def get(self, group, key, default=None):
        if key not in self.config[group]:
            return default
        return self.config[group][key] 
    def getBot(self,key, default=None):
        return self.get("bot", key, default)
    def getBotToken(self):
        return self.get("bot", 'token')
    def getBotToken(self):
        return self.get("bot", 'token')
    def getBotWhitelist(self,default=None):
        whitelist = self.get("bot", 'whitelist', default)
        return { int(uid) for uid in whitelist if str(uid).isdigit()}
    def getCloud(self,key, default=None):
        return self.get("ycloud", key, default)
    def getCloudKey(self):
        return self.getCloud("api_key")
    def getCloudFolder(self):
        return self.getCloud("folder_id")
    def getYandex(self,key, default=None):
        return self.get("yandex", key, default)

# Load the configuration
with open('config.yml', 'r', encoding='utf-8') as f:
    config_data = yaml.safe_load(f)

config = Config(config_data)

# Yandex Cloud configuration
SYSTEM_PROMPT = config.getYandex('system_prompt')
SPEECH_API_KEY = config.getYandex('speech_api_key')
SYSTEM_MODEL = config.getYandex('model')
INDEX_KEY = config.getYandex('index')
BOT_KEY = config.getYandex('key')
USER_INDEX_KEY = config.getYandex('user_index')

# S3 configuration
S3_ACCESS_KEY = config.get('s3', 'access_key')
S3_SECRET_KEY = config.get('s3', 'secret_key')

# MCP configuration
MCP_B2B_INN_CHECK_URL = config.get('mcp', 'b2b_inn_check_url')

# ICS configuration
ICS_API_KEY = config.get('ics', 'api_key')
ICS_URL = config.get('ics', 'url')
ICS_PULLING_INTERVAL = config.get('ics', 'pulling_interval')
