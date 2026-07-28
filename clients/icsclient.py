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
        self, chat_id: str, chat_type: str, client_type: str, url: str, name: str = ""
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
            if name:
                payload["name"] = name
            headers = {"X-Auth-Token": self.api_key, "Content-Type": "application/json"}
            logger.info(f"Registering calendar for chat {chat_id} at {endpoint}")
            response = requests.post(endpoint, json=payload, headers=headers)
            if response.status_code in (200, 201):
                label = f" ({name})" if name else ""
                logger.info(
                    f"Calendar registered successfully for chat {chat_id}{label}"
                )
                return True
            else:
                logger.error(
                    f"Failed to register calendar for chat {chat_id}: {response.status_code} {response.text}"
                )
                return False
        except Exception as e:
            logger.error(f"Error registering calendar for chat {chat_id}: {str(e)}")
            return False

    def get_calendars(self, user_id: str):
        """List calendars for a user"""
        try:
            params = {"api_key": self.api_key, "user_id": user_id}
            response = requests.get(f"{self.base_url}/calendars", params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get("calendars", [])
            else:
                logger.error(
                    f"Failed to get calendars: {response.status_code} {response.text}"
                )
                return None
        except Exception as e:
            logger.error(f"Error getting calendars: {str(e)}")
            return None

    def delete_calendar(self, calendar_id: str, user_id: str) -> bool:
        """Delete a calendar by id"""
        try:
            params = {"api_key": self.api_key, "user_id": user_id}
            response = requests.delete(
                f"{self.base_url}/calendars/{calendar_id}", params=params
            )
            if response.status_code in (200, 204):
                logger.info(f"Calendar {calendar_id} deleted successfully")
                return True
            else:
                logger.error(
                    f"Failed to delete calendar {calendar_id}: {response.status_code} {response.text}"
                )
                return False
        except Exception as e:
            logger.error(f"Error deleting calendar {calendar_id}: {str(e)}")
            return False

    def update_calendar(self, calendar_id: str, user_id: str, **fields) -> bool:
        """Update calendar fields (name, url, client_type, timezone)"""
        try:
            params = {"api_key": self.api_key, "user_id": user_id}
            response = requests.put(
                f"{self.base_url}/calendars/{calendar_id}",
                params=params,
                json=fields,
            )
            if response.status_code in (200, 204):
                logger.info(f"Calendar {calendar_id} updated: {fields}")
                return True
            else:
                logger.error(
                    f"Failed to update calendar {calendar_id}: {response.status_code} {response.text}"
                )
                return False
        except Exception as e:
            logger.error(f"Error updating calendar {calendar_id}: {str(e)}")
            return False

    def create_event(self, calendar_id: str, user_id: str, **fields) -> bool:
        """Create an event in a calendar"""
        try:
            params = {"api_key": self.api_key, "user_id": user_id}
            response = requests.post(
                f"{self.base_url}/calendars/{calendar_id}/events",
                params=params,
                json=fields,
            )
            if response.status_code in (200, 201):
                logger.info(
                    f"Event created in calendar {calendar_id}: {fields.get('summary', '')}"
                )
                return True
            else:
                logger.error(
                    f"Failed to create event in calendar {calendar_id}: {response.status_code} {response.text}"
                )
                return False
        except Exception as e:
            logger.error(f"Error creating event in calendar {calendar_id}: {str(e)}")
            return False
