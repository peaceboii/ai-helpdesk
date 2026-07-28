from typing import Dict, Any
from app.models.ticket import Ticket
from app.services.ticket_processor import TicketProcessor
from app.services.notification_service import NotificationService
from app.services.database_service import TicketRepository, IntegrationRepository

class TicketService:
    def __init__(self):
        self.processor = TicketProcessor()

    def process_incoming_ticket(self, ticket: Ticket) -> Dict[str, Any]:
        """
        Orchestrates ingestion, classification, database storage, metrics logging, 
        and customer auto-acknowledgement.
        """
        # Ensure it has a ticket ID
        if not ticket.ticket_id:
            ticket.ticket_id = TicketRepository.get_next_ticket_id()
            
        # Process using the ticket pipeline
        res = self.processor.process(ticket)
        
        # Deduce integration ID for metrics
        source_lower = ticket.source.lower()
        integration_id = "api"
        if "email" in source_lower:
            integration_id = "email"
        elif "telegram" in source_lower:
            integration_id = "telegram"
        elif "slack" in source_lower:
            integration_id = "slack"
        elif "whatsapp" in source_lower:
            integration_id = "whatsapp"
        elif "web" in source_lower:
            integration_id = "website"
            
        if res.get("status") == "Rejected":
            IntegrationRepository.update_logs(
                integration_id,
                connection_status="Connected",
                increment_errors=True,
                add_log_message=f"Rejected ticket: {res.get('reason')}"
            )
            return res
            
        if res.get("status") == "Spam":
            IntegrationRepository.update_logs(
                integration_id,
                connection_status="Connected",
                increment_processed=True,
                add_log_message=f"Flagged SPAM ticket: {ticket.ticket_id} from {ticket.email}"
            )
            return res
            
        # Auto-Response dispatch
        auto_response = res.get("auto_response", "")
        if auto_response:
            NotificationService.send_auto_acknowledgement(ticket, auto_response)
            
        # Update integration stats
        IntegrationRepository.update_logs(
            integration_id,
            connection_status="Connected",
            last_ticket_created=ticket.ticket_id,
            increment_processed=True,
            add_log_message=f"Processed ticket {ticket.ticket_id} (Category: {ticket.category}, Priority: {ticket.priority})"
        )
        
        return res
