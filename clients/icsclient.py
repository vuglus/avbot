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
        print(f"!!!...{ICS_API_KEY}")

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

    def compare_events(self, old_events: List[Dict], new_events: List[Dict]) -> Dict[str, List[Dict]]:
        """Compare old and new events to find added, removed, and modified events"""
        # Create dictionaries for easier comparison
        old_events_dict = {event['id']: event for event in old_events}
        new_events_dict = {event['id']: event for event in new_events}
        
        added = []
        removed = []
        modified = []
        
        # Check for added events (in new but not in old)
        for event_id, event in new_events_dict.items():
            if event_id not in old_events_dict:
                added.append(event)
            elif old_events_dict[event_id] != event:
                modified.append({
                    'old': old_events_dict[event_id],
                    'new': event
                })
        
        # Check for removed events (in old but not in new)
        for event_id, event in old_events_dict.items():
            if event_id not in new_events_dict:
                removed.append(event)
        
        return {
            'added': added,
            'removed': removed,
            'modified': modified
        }