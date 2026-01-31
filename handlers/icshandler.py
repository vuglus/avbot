import asyncio
import logging
from typing import Dict, List, Any, Optional
from telegram import Bot
from services.config_service import ICS_SYSTEM_PROMPT
from services.yandexgpt_service import ask_yandexgpt

# Set up logging
logger = logging.getLogger(__name__)

class ICSHandler:
    """Handler for forming messages and sending ICS notifications"""
    
    def __init__(self, config: Dict[str, Any], bot: Bot):
        self.config = config
        self.bot = bot
        self.system_prompt = ICS_SYSTEM_PROMPT
        self.whitelist = config.get('bot', {}).get('whitelist', [])
        self.user_states: Dict[int, List[Dict]] = {}  # In-memory state storage

    def format_changes(self, changes: Dict[str, List[Dict]]) -> str:
        """Format changes into a string representation"""
        # If no changes, return empty string
        if not any(changes.values()):
            return ""
        
        summary_parts = []
        
        if changes['added']:
            summary_parts.append(f"Добавлено событий: {len(changes['added'])}")
            for event in changes['added']:
                summary_parts.append(f"- {event['title']} ({event['start_datetime']})")
        
        if changes['removed']:
            summary_parts.append(f"Удалено событий: {len(changes['removed'])}")
            for event in changes['removed']:
                summary_parts.append(f"- {event['title']} ({event['start_datetime']})")
        
        if changes['modified']:
            summary_parts.append(f"Изменено событий: {len(changes['modified'])}")
            for change in changes['modified']:
                summary_parts.append(f"- {change['new']['title']} ({change['new']['start_datetime']})")
        
        return "\n".join(summary_parts)

    async def send_notification(self, user_id: int, changes: Dict[str, List[Dict]]):
        """Send notification to user via Telegram using YandexGPT"""
        try:
            # Format changes into a string
            changes_text = self.format_changes(changes)
            
            # Only send if there are actual changes
            if changes_text:
                # Create prompt for YandexGPT
                prompt = f"{self.system_prompt}\n\n{changes_text}"
                
                # Get response from YandexGPT
                response = ask_yandexgpt(prompt, user_id)
                
                # Send the response to the user
                await self.bot.send_message(
                    chat_id=user_id,
                    text=f"Обновления в календаре:\n\n{response}"
                )
                logger.info(f"Sent notification to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send notification to user {user_id}: {str(e)}")

    def check_user_events(self, user_id: int, new_events: List[Dict]):
        """Check events for a specific user and send notifications if there are changes"""
        try:
            # Get old events from memory
            old_events = self.user_states.get(user_id, [])
            
            # Compare events using the client's method
            from clients.icsclient import ICSClient
            ics_client = ICSClient(self.config)
            changes = ics_client.compare_events(old_events, new_events)
            
            # Only send notification if there are actual changes
            if any(changes.values()):
                # Schedule the async notification
                asyncio.create_task(self.send_notification(user_id, changes))
                # Update in-memory state only if there were changes
                self.user_states[user_id] = new_events
            
        except Exception as e:
            logger.error(f"Error checking events for user {user_id}: {str(e)}")

    async def monitor_loop(self, ics_client):
        """Main monitoring loop"""
        logger.info("Starting ICS monitoring loop")
        
        try:
            while True:
                logger.info("Checking for event updates...")
                
                # Check events for all whitelisted users
                for user_id in self.whitelist:
                    # Fetch new events using the client
                    new_events = ics_client.fetch_events(user_id)
                    # Check and send notifications
                    self.check_user_events(user_id, new_events)
                
                # Wait for the next interval
                logger.info(f"Waiting {ics_client.pulling_interval} seconds until next check...")
                await asyncio.sleep(ics_client.pulling_interval)
                
        except asyncio.CancelledError:
            logger.info("Monitoring loop cancelled")
        except Exception as e:
            logger.error(f"Error in monitoring loop: {str(e)}")