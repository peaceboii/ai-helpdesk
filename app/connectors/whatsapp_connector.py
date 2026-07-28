import requests
from typing import Dict, Any, Optional
from datetime import datetime
from app.connectors.base import BaseConnector
from app.models.ticket import Ticket
from app.services.database_service import TicketRepository

class WhatsAppConnector(BaseConnector):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.phone_number_id = config.get("phone_number_id", "")
        self.access_token = config.get("access_token", "")
        self.verify_token = config.get("verify_token", "")
        self.webhook_url = config.get("webhook_url", "")

    def ingest(self, payload: Dict[str, Any], attachment_name: Optional[str] = None, attachment_data: Optional[bytes] = None) -> Ticket:
        """
        Parses WhatsApp message payload.
        Expected keys: from_number, profile_name, text
        """
        ticket_id = TicketRepository.get_next_ticket_id()
        profile_name = payload.get("profile_name", "WhatsApp User")
        from_number = payload.get("from_number", "Unknown")
        text = payload.get("text", "")
        
        # Split text into subject (first line) and body (rest)
        lines = text.split("\n", 1)
        subject = lines[0] if lines else "WhatsApp Message"
        if len(subject) > 60:
            subject = subject[:57] + "..."
        body = lines[1] if len(lines) > 1 else text
        
        ticket = Ticket(
            ticket_id=ticket_id,
            customer_name=profile_name,
            email=f"{from_number.replace('+', '')}@whatsapp.net",
            source="WhatsApp",
            subject=subject,
            body=body,
            attachment_name=attachment_name,
            attachment_data=attachment_data
        )
        
        # Store phone number in entities
        ticket.entities["Phone"] = from_number
        return ticket

    def test_connection(self) -> str:
        """
        Tests WhatsApp credentials by calling Meta's Graph API.
        Returns: 'Connected', 'Invalid Token', or 'Disconnected'
        """
        if not self.phone_number_id or not self.access_token:
            return "Disconnected"
            
        if self.phone_number_id == "mock_phone_id":
            return "Connected"
            
        try:
            url = f"https://graph.facebook.com/v17.0/{self.phone_number_id}"
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                return "Connected"
            elif resp.status_code in [400, 401, 403]:
                return "Invalid Token"
            return "Disconnected"
        except Exception as e:
            print(f"WhatsApp connection testing error: {e}")
            return "Disconnected"

    def download_media(self, media_id: str) -> Optional[bytes]:
        """
        Downloads media (image, document, voice note) from WhatsApp Business API.
        """
        if not self.access_token or self.phone_number_id == "mock_phone_id":
            return b"Simulated whatsapp media file bytes content."
            
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}"
            }
            # 1. Fetch media URL
            url = f"https://graph.facebook.com/v17.0/{media_id}"
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                return None
            download_url = resp.json().get("url")
            if not download_url:
                return None
                
            # 2. Download the bytes
            dl_resp = requests.get(download_url, headers=headers, timeout=20)
            if dl_resp.status_code == 200:
                return dl_resp.content
        except Exception as e:
            print(f"WhatsApp media download error: {e}")
        return None
