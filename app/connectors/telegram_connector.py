from typing import Dict, Any, Optional
from app.connectors.base import BaseConnector
from app.models.ticket import Ticket
from app.services.database_service import TicketRepository

class TelegramConnector(BaseConnector):
    def ingest(self, payload: Dict[str, Any], attachment_name: Optional[str] = None, attachment_data: Optional[bytes] = None) -> Ticket:
        """
        Parses Telegram webhook event payload.
        Expected format: {"chat_id": 123456, "first_name": "John", "username": "john_tg", "text": "message content"}
        """
        ticket_id = TicketRepository.get_next_ticket_id()
        first_name = payload.get("first_name", "Telegram User")
        username = payload.get("username", "unknown")
        text = payload.get("text", "")
        
        # Parse subject/body
        lines = text.split("\n", 1)
        subject = lines[0] if lines else "Telegram Ticket"
        if len(subject) > 60:
            subject = subject[:57] + "..."
            
        body = lines[1] if len(lines) > 1 else text
        
        return Ticket(
            ticket_id=ticket_id,
            customer_name=first_name,
            email=f"{username}@telegram.org",
            source="Telegram Bot",
            subject=subject,
            body=body,
            attachment_name=attachment_name,
            attachment_data=attachment_data
        )
