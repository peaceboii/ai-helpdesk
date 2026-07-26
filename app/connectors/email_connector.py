import imaplib
import email
from email.header import decode_header
from typing import Dict, Any, List, Optional
import os
from datetime import datetime
from app.connectors.base import BaseConnector
from app.models.ticket import Ticket
from app.services.database_service import TicketRepository

class EmailConnector(BaseConnector):
    def __init__(self, config: Dict[str, Any]):
        self.host = config.get("host", "imap.example.com")
        self.port = config.get("port", 993)
        self.use_ssl = config.get("use_ssl", True)
        self.username = config.get("username", "support@example.com")
        self.password = config.get("password", "")

    def ingest(self, payload: Dict[str, Any], attachment_name: Optional[str] = None, attachment_data: Optional[bytes] = None) -> Ticket:
        """
        Manually processes a single dictionary representing an email payload (for manual trigger/API).
        """
        ticket_id = TicketRepository.get_next_ticket_id()
        return Ticket(
            ticket_id=ticket_id,
            customer_name=payload.get("sender_name", payload.get("sender", "Unknown")),
            email=payload.get("sender", "unknown@example.com"),
            source="Email",
            subject=payload.get("subject", "No Subject"),
            body=payload.get("body", ""),
            attachment_name=attachment_name,
            attachment_data=attachment_data
        )

    def fetch_unread_emails(self) -> List[Ticket]:
        """
        Fetches unread emails from the IMAP inbox.
        If it's configured as the mock host 'imap.example.com', it returns a simulated email list for demo.
        """
        if self.host == "imap.example.com" or not self.password or self.password == "mock_password":
            return self._get_simulated_emails()
            
        tickets = []
        try:
            # Connect to IMAP
            if self.use_ssl:
                mail = imaplib.IMAP4_SSL(self.host, self.port)
            else:
                mail = imaplib.IMAP4(self.host, self.port)
                
            mail.login(self.username, self.password)
            mail.select("inbox")
            
            status, messages = mail.search(None, 'UNSEEN')
            if status != "OK":
                return []
                
            for num in messages[0].split():
                status, data = mail.fetch(num, '(RFC822)')
                if status != "OK":
                    continue
                    
                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                # Decode Subject
                subject_header = msg.get("Subject", "No Subject")
                subject, encoding = decode_header(subject_header)[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding or "utf-8", errors="ignore")
                    
                # Decode Sender
                from_header = msg.get("From", "unknown@example.com")
                sender_name = "Unknown"
                sender_email = from_header
                if "<" in from_header:
                    sender_name, sender_email = from_header.split("<", 1)
                    sender_name = sender_name.strip().strip('"')
                    sender_email = sender_email.strip().rstrip(">")
                    
                # Extract Body & Attachments
                body = ""
                att_name = None
                att_data = None
                
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))
                        
                        if content_type == "text/plain" and "attachment" not in content_disposition:
                            payload_data = part.get_payload(decode=True)
                            body += payload_data.decode(part.get_content_charset() or "utf-8", errors="ignore")
                        elif "attachment" in content_disposition:
                            filename = part.get_filename()
                            if filename:
                                att_name = filename
                                att_data = part.get_payload(decode=True)
                else:
                    body = msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8", errors="ignore")
                
                # Mark as read
                mail.store(num, '+FLAGS', '\\Seen')
                
                # Create Ticket
                ticket_id = TicketRepository.get_next_ticket_id()
                tickets.append(Ticket(
                    ticket_id=ticket_id,
                    customer_name=sender_name or sender_email,
                    email=sender_email,
                    source="Email",
                    subject=subject,
                    body=body,
                    attachment_name=att_name,
                    attachment_data=att_data
                ))
            mail.close()
            mail.logout()
        except Exception as e:
            print(f"IMAP Error: {e}. Falling back to empty or simulated emails.")
            
        return tickets

    def _get_simulated_emails(self) -> List[Ticket]:
        """Returns mock emails for demonstration purposes."""
        simulated = [
            {
                "sender_name": "Alice Johnson",
                "sender": "alice.j@example.com",
                "subject": "Urgent: Billing issue - invoice incorrect",
                "body": "Hi Support team, I noticed that invoice INV-2026-042 displays double the agreed amount. Please fix this asap as our account is down."
            },
            {
                "sender_name": "Robert Smith",
                "sender": "robert.smith@corp.com",
                "subject": "Leave request for August",
                "body": "Hello HR, I need to request 5 days off from August 10th to 15th for family reasons. Thanks, Robert Employee ID: EMP-9823"
            }
        ]
        tickets = []
        for i, item in enumerate(simulated):
            ticket_id = TicketRepository.get_next_ticket_id()
            # Stagger timestamps slightly
            time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            tickets.append(Ticket(
                ticket_id=ticket_id,
                customer_name=item["sender_name"],
                email=item["sender"],
                source="Email",
                subject=item["subject"],
                body=item["body"],
                created_time=time_str
            ))
        return tickets
