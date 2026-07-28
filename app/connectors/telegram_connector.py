import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.connectors.base import BaseConnector
from app.models.ticket import Ticket
from app.services.database_service import TicketRepository

class TelegramConnector(BaseConnector):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.bot_token = config.get("bot_token", "")
        self.allowed_chats = [c.strip() for c in config.get("allowed_chats", "").split(",") if c.strip()]
        self.webhook_url = config.get("webhook_url", "")

    def ingest(self, payload: Dict[str, Any], attachment_name: Optional[str] = None, attachment_data: Optional[bytes] = None) -> Ticket:
        """
        Parses Telegram webhook/polling event payload.
        Expected keys: chat_id, first_name, username, text
        """
        ticket_id = TicketRepository.get_next_ticket_id()
        first_name = payload.get("first_name", "Telegram User")
        username = payload.get("username", "unknown")
        text = payload.get("text", "")
        chat_id = payload.get("chat_id")
        
        # Split text into subject (first line) and body (rest)
        lines = text.split("\n", 1)
        subject = lines[0] if lines else "Telegram Ticket"
        if len(subject) > 60:
            subject = subject[:57] + "..."
        body = lines[1] if len(lines) > 1 else text
        
        ticket = Ticket(
            ticket_id=ticket_id,
            customer_name=first_name,
            email=f"{username}@telegram.org",
            source="Telegram",
            subject=subject,
            body=body,
            attachment_name=attachment_name,
            attachment_data=attachment_data
        )
        
        ticket.entities["Telegram Chat ID"] = str(chat_id)
        return ticket

    def test_connection(self) -> str:
        """
        Tests Telegram bot connection by calling getMe.
        Returns: 'Connected', 'Invalid Token', or 'Disconnected'
        """
        if not self.bot_token:
            return "Disconnected"
            
        if self.bot_token == "mock_token":
            return "Connected"
            
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    return "Connected"
            elif resp.status_code in [401, 404]:
                return "Invalid Token"
            return "Disconnected"
        except Exception as e:
            print(f"Telegram connection error: {e}")
            return "Disconnected"

    def download_file(self, file_id: str) -> Optional[bytes]:
        """
        Downloads a file from Telegram using file_id.
        """
        if not self.bot_token or self.bot_token == "mock_token":
            return b"Simulated telegram file bytes content."
            
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getFile"
            resp = requests.get(url, params={"file_id": file_id}, timeout=10)
            if resp.status_code != 200 or not resp.json().get("ok"):
                return None
            file_path = resp.json()["result"]["file_path"]
            
            download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
            dl_resp = requests.get(download_url, timeout=20)
            if dl_resp.status_code == 200:
                return dl_resp.content
        except Exception as e:
            print(f"Error downloading file from Telegram: {e}")
        return None

    def process_polling_updates(self, offset: int, ticket_processor_callback) -> int:
        """
        Fetches updates via long polling and processes them.
        Returns the next offset index.
        """
        if not self.bot_token or self.bot_token == "mock_token":
            return offset

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
            params = {"offset": offset, "timeout": 5, "allowed_updates": ["message"]}
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code != 200:
                return offset
                
            data = resp.json()
            if not data.get("ok") or not data.get("result"):
                return offset
                
            max_update_id = offset
            for update in data["result"]:
                update_id = update["update_id"]
                max_update_id = max(max_update_id, update_id)
                
                message = update.get("message")
                if not message:
                    continue
                    
                chat = message.get("chat", {})
                chat_id = chat.get("id")
                from_user = message.get("from", {})
                first_name = from_user.get("first_name", "Telegram User")
                username = from_user.get("username", "unknown")
                
                # Allowed Chats validation
                if self.allowed_chats:
                    chat_str = str(chat_id)
                    username_str = f"@{username}".lower()
                    if chat_str not in self.allowed_chats and username_str not in self.allowed_chats:
                        print(f"Telegram message ignored: chat_id {chat_id} is not allowed.")
                        continue
                
                text = message.get("text", "")
                caption = message.get("caption", "")
                if caption and not text:
                    text = caption
                    
                attachment_name = None
                attachment_data = None
                
                # Support Photo, Document, Voice
                if "photo" in message:
                    photo_list = message["photo"]
                    largest_photo = photo_list[-1]
                    file_id = largest_photo["file_id"]
                    attachment_name = f"photo_{file_id}.jpg"
                    attachment_data = self.download_file(file_id)
                    if not text:
                        text = f"Telegram photo attachment: {attachment_name}"
                elif "document" in message:
                    doc = message["document"]
                    file_id = doc["file_id"]
                    attachment_name = doc.get("file_name", f"doc_{file_id}")
                    attachment_data = self.download_file(file_id)
                    if not text:
                        text = f"Telegram document attachment: {attachment_name}"
                elif "voice" in message:
                    voice = message["voice"]
                    file_id = voice["file_id"]
                    attachment_name = f"voice_{file_id}.ogg"
                    attachment_data = self.download_file(file_id)
                    if not text:
                        text = f"Telegram voice attachment: {attachment_name}"
                
                payload = {
                    "chat_id": chat_id,
                    "first_name": first_name,
                    "username": username,
                    "text": text or "No Text (Empty message)"
                }
                
                ticket = self.ingest(payload, attachment_name, attachment_data)
                ticket_processor_callback(ticket)
                
            return max_update_id + 1
        except Exception as e:
            print(f"Telegram polling error: {e}")
            raise e
