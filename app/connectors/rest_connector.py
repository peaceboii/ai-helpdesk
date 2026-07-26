from typing import Dict, Any, Optional
from app.connectors.base import BaseConnector
from app.models.ticket import Ticket
from app.services.database_service import TicketRepository

class RESTConnector(BaseConnector):
    def ingest(self, payload: Dict[str, Any], attachment_name: Optional[str] = None, attachment_data: Optional[bytes] = None) -> Ticket:
        """
        Parses API POST /api/tickets payload.
        Expected format: {"customer_name": "Bob", "email": "bob@example.com", "subject": "title", "description": "desc", "source": "REST API"}
        """
        ticket_id = TicketRepository.get_next_ticket_id()
        return Ticket(
            ticket_id=ticket_id,
            customer_name=payload.get("customer_name", "API User"),
            email=payload.get("email", "api@example.com"),
            source=payload.get("source", "REST API"),
            subject=payload.get("subject", "API Ticket"),
            body=payload.get("description", payload.get("body", "")),
            attachment_name=attachment_name,
            attachment_data=attachment_data
        )
