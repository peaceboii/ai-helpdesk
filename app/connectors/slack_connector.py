from typing import Dict, Any, Optional
from app.connectors.base import BaseConnector
from app.models.ticket import Ticket
from app.services.database_service import TicketRepository

class SlackConnector(BaseConnector):
    def ingest(self, payload: Dict[str, Any], attachment_name: Optional[str] = None, attachment_data: Optional[bytes] = None) -> Ticket:
        """
        Parses Slack webhook event payload.
        Expected format: {"user_id": "U1234", "user_name": "slack_user", "text": "Message content", "channel": "C999"}
        """
        ticket_id = TicketRepository.get_next_ticket_id()
        user_name = payload.get("user_name", "Slack User")
        user_id = payload.get("user_id", "Unknown")
        text = payload.get("text", "")
        
        # Split text into subject (first line) and body (rest)
        lines = text.split("\n", 1)
        subject = lines[0] if lines else "Slack Ticket"
        if len(subject) > 60:
            subject = subject[:57] + "..."
            
        body = lines[1] if len(lines) > 1 else text
        
        return Ticket(
            ticket_id=ticket_id,
            customer_name=user_name,
            email=f"{user_id}@slack.com",  # Mock email for Slack user ID
            source="Slack Bot",
            subject=subject,
            body=body,
            attachment_name=attachment_name,
            attachment_data=attachment_data
        )
