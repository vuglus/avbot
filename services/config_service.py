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

