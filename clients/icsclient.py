import requests
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from services.config_service import ICS_API_KEY, ICS_URL, ICS_PULLING_INTERVAL

# Set up logging
logger = logging.getLogger(__name__)

class ICSClient:
    """Client for fetching and parsing ICS events data"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = ICS_API_KEY
        self.base_url = ICS_URL
        self.whitelist = config.get('bot', {}).get('whitelist', [])
        self.pulling_interval = ICS_PULLING_INTERVAL * 60  # Convert to seconds

    def fetch_events(self, user_id: int) -> List[Dict]:
        """Fetch events for a specific user from the API"""
        try:
            url = f"{self.base_url}?api_key={self.api_key}&user_id={user_id}"
            logger.info(f"Fetching events for user {user_id} from {url}")
            
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                return data.get('events', [])
            else:
                logger.error(f"Failed to fetch events for user {user_id}: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error fetching events for user {user_id}: {str(e)}")
            return []

    def compare_events(self, old_events, new_events):
        def key(event):
            return event["uid"]  # стабильный идентификатор

        def normalize(event):
            # Create a normalized version of the event for comparison
            # This ensures we only compare relevant fields
            return {
                "uid": event.get("uid"),
                "title": event.get("title"),
                "start_datetime": event.get("start_datetime"),
                "end_datetime": event.get("end_datetime"),
                "description": event.get("description")
            }

        old_events_dict = {key(e): e for e in old_events}
        new_events_dict = {key(e): e for e in new_events}

        added = []
        removed = []
        modified = []

        for uid, new_event in new_events_dict.items():
            old_event = old_events_dict.get(uid)

            if not old_event:
                added.append(new_event)
                continue

            if normalize(old_event) != normalize(new_event):
                modified.append({
                    "old": old_event,
                    "new": new_event
                })

        for uid, old_event in old_events_dict.items():
            if uid not in new_events_dict:
                removed.append(old_event)

        return {
            "added": added,
            "removed": removed,
            "modified": modified
        }