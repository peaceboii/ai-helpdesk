from typing import Dict, Any, Optional
from app.connectors.base import BaseConnector
from app.models.ticket import Ticket
from app.services.database_service import TicketRepository

class WhatsAppConnector(BaseConnector):
    def ingest(self, payload: Dict[str, Any], attachment_name: Optional[str] = None, attachment_data: Optional[bytes] = None) -> Ticket:
        """
        Parses WhatsApp webhook event payload.
        Expected format: {"from_number": "+15550199", "profile_name": "Alice", "text": "message text"}
        """
        ticket_id = TicketRepository.get_next_ticket_id()
        profile_name = payload.get("profile_name", "WhatsApp User")
        from_number = payload.get("from_number", "Unknown")
        text = payload.get("text", "")
        
        lines = text.split("\n", 1)
        subject = lines[0] if lines else "WhatsApp Message"
        if len(subject) > 60:
            subject = subject[:57] + "..."
            
        body = lines[1] if len(lines) > 1 else text
        
        return Ticket(
            ticket_id=ticket_id,
            customer_name=profile_name,
            email=f"{from_number.replace('+', '')}@whatsapp.net",
            source="WhatsApp",
            subject=subject,
            body=body,
            attachment_name=attachment_name,
            attachment_data=attachment_data
        )
