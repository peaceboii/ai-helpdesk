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
            
            # Forward copy of initial reply and ticket details to assigned department
            forward_sub = f"[TICKET FORWARDED] New Ingestion: {ticket.ticket_id} ({ticket.source})"
            forward_body = (
                f"Dear Team,\n\n"
                f"A new ticket has been ingested and routed to your department.\n\n"
                f"--- Ticket Details ---\n"
                f"ID: {ticket.ticket_id}\n"
                f"Source: {ticket.source}\n"
                f"Customer Name: {ticket.customer_name}\n"
                f"Customer Email: {ticket.email}\n"
                f"Category: {ticket.category}\n"
                f"Priority: {ticket.priority}\n"
                f"Assigned Team: {ticket.assigned_team}\n\n"
                f"--- Auto-Response Sent to Customer ---\n"
                f"{auto_response}\n"
            )
            NotificationService.notify_department(ticket, forward_sub, forward_body)
            
        # Update integration stats
        IntegrationRepository.update_logs(
            integration_id,
            connection_status="Connected",
            last_ticket_created=ticket.ticket_id,
            increment_processed=True,
            add_log_message=f"Processed ticket {ticket.ticket_id} (Category: {ticket.category}, Priority: {ticket.priority})"
        )
        
        return res

    def update_status(self, ticket_id: str, new_status: str) -> None:
        """
        Updates the ticket status, auto-generates a status update reply, 
        sends it to the customer via their original communication medium,
        and forwards a copy to the department contact.
        """
        ticket = TicketRepository.get_ticket(ticket_id)
        if not ticket:
            return
            
        old_status = ticket.status
        if old_status == new_status:
            return
            
        # Save new status to repository
        TicketRepository.update_ticket_status(ticket_id, new_status)
        ticket.status = new_status
        
        # Format the customer status update message
        update_text = (
            f"Hello {ticket.customer_name},\n\n"
            f"The status of your support request has been updated.\n\n"
            f"Ticket ID: {ticket.ticket_id}\n"
            f"New Status: {new_status}\n"
            f"Category: {ticket.category}\n"
            f"Priority: {ticket.priority}\n\n"
            f"If you have any further questions, please reply directly through this channel.\n"
            f"AI Helpdesk Automation Platform"
        )
        
        # Send status update response back to the customer on the same channel
        NotificationService.send_auto_acknowledgement(ticket, update_text)
        
        # Forward status update details to department
        forward_sub = f"[TICKET STATUS UPDATE] {ticket.ticket_id} changed to {new_status}"
        forward_body = (
            f"Dear Team,\n\n"
            f"The status of ticket {ticket.ticket_id} has been updated to {new_status}.\n\n"
            f"--- Status Update Sent to Customer ---\n"
            f"{update_text}\n"
        )
        NotificationService.notify_department(ticket, forward_sub, forward_body)
