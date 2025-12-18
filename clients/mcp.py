import requests

class MCPClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def call(self, tool_name: str, arguments: dict) -> dict:
        r = requests.post(
            f"{self.base_url}/{tool_name}",
            json=arguments,
            timeout=10
        )
        r.raise_for_status()
        return r.json()
