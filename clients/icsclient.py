import requests
import logging
from services.config_service import Config

logger = logging.getLogger(__name__)


class ICSClient:
    """Client for ICS/calendar service API."""

    def __init__(self, config: Config):
        self.config = config
        self.api_key = config.get("ics", "api_key")
        self.base_url = config.get("ics", "url")

    def register_calendar(
        self, chat_id: str, chat_type: str, client_type: str, url: str
    ) -> bool:
        """Register a calendar for a user by POSTing to the ICS service"""
        try:
            endpoint = f"{self.base_url}/calendars"
            payload = {
                "chat_id": chat_id,
                "chat_type": chat_type,
                "client_type": client_type,
                "url": url,
            }
            headers = {"X-Auth-Token": self.api_key, "Content-Type": "application/json"}
            logger.info(f"Registering calendar for chat {chat_id} at {endpoint}")
            response = requests.post(endpoint, json=payload, headers=headers)
            if response.status_code in (200, 201):
                logger.info(f"Calendar registered successfully for chat {chat_id}")
                return True
            else:
                logger.error(
                    f"Failed to register calendar for chat {chat_id}: {response.status_code} {response.text}"
                )
                return False
        except Exception as e:
            logger.error(f"Error registering calendar for chat {chat_id}: {str(e)}")
            return False
