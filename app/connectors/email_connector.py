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
        self.config = config
        self.host = config.get("email_imap_host", config.get("host", "imap.example.com"))
        try:
            self.port = int(config.get("email_imap_port", config.get("port", 993)))
        except ValueError:
            self.port = 993
        self.use_ssl = True
        self.username = config.get("email_address", config.get("username", ""))
        self.password = config.get("email_app_password", config.get("password", ""))

    def ingest(self, payload: Dict[str, Any], attachment_name: Optional[str] = None, attachment_data: Optional[bytes] = None) -> Ticket:
        """
        Manually processes a single email payload (via API / webhook).
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

    def test_connection(self) -> str:
        """
        Tests the IMAP server connection.
        Returns: 'Connected', 'Authentication Failed', or 'Disconnected'
        """
        if not self.username or not self.password:
            return "Disconnected"
            
        if self.host == "imap.example.com":
            return "Connected"
            
        try:
            if self.use_ssl:
                mail = imaplib.IMAP4_SSL(self.host, self.port, timeout=10)
            else:
                mail = imaplib.IMAP4(self.host, self.port, timeout=10)
                
            mail.login(self.username, self.password)
            mail.logout()
            return "Connected"
        except imaplib.IMAP4.error as ae:
            print(f"IMAP Auth error: {ae}")
            return "Authentication Failed"
        except Exception as e:
            print(f"IMAP Connection error: {e}")
            return "Disconnected"

    def process_and_move_emails(self, ticket_processor_callback) -> List[Ticket]:
        """
        Polls IMAP, extracts unread messages, processes them via callback,
        and moves them to the Processed folder.
        """
        if self.host == "imap.example.com" or not self.password:
            # Simulated emails for demo if using default/fallback settings
            emails = self._get_simulated_emails()
            for t in emails:
                ticket_processor_callback(t)
            return emails

        tickets = []
        try:
            if self.use_ssl:
                mail = imaplib.IMAP4_SSL(self.host, self.port, timeout=15)
            else:
                mail = imaplib.IMAP4(self.host, self.port, timeout=15)
                
            mail.login(self.username, self.password)
            
            unread_folder = self.config.get("unread_folder", "INBOX")
            mail.select(unread_folder)
            
            status, messages = mail.search(None, 'UNSEEN')
            if status != "OK" or not messages[0]:
                mail.logout()
                return []
                
            processed_folder = self.config.get("processed_folder", "Processed")
            
            for num in messages[0].split():
                status, data = mail.fetch(num, '(RFC822)')
                if status != "OK" or not data or not data[0]:
                    continue
                    
                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                # Subject Decoding
                subject_header = msg.get("Subject", "No Subject")
                subject, encoding = decode_header(subject_header)[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding or "utf-8", errors="ignore")
                    
                # Sender Decoding
                from_header = msg.get("From", "unknown@example.com")
                sender_name = "Unknown"
                sender_email = from_header
                if "<" in from_header:
                    sender_name, sender_email = from_header.split("<", 1)
                    sender_name = sender_name.strip().strip('"')
                    sender_email = sender_email.strip().rstrip(">")
                    
                # Extract Body & Attachments
                body = ""
                attachments = []
                
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))
                        
                        if content_type == "text/plain" and "attachment" not in content_disposition:
                            payload_data = part.get_payload(decode=True)
                            if payload_data:
                                body += payload_data.decode(part.get_content_charset() or "utf-8", errors="ignore")
                        elif "attachment" in content_disposition:
                            filename = part.get_filename()
                            if filename:
                                decoded_filename, fn_encoding = decode_header(filename)[0]
                                if isinstance(decoded_filename, bytes):
                                    filename = decoded_filename.decode(fn_encoding or "utf-8", errors="ignore")
                                att_data = part.get_payload(decode=True)
                                if att_data:
                                    attachments.append((filename, att_data))
                else:
                    payload_data = msg.get_payload(decode=True)
                    if payload_data:
                        body = payload_data.decode(msg.get_content_charset() or "utf-8", errors="ignore")
                
                ticket_id = TicketRepository.get_next_ticket_id()
                
                att_name = None
                att_data = None
                if attachments:
                    att_name = attachments[0][0]
                    att_data = attachments[0][1]
                    
                ticket = Ticket(
                    ticket_id=ticket_id,
                    customer_name=sender_name or sender_email,
                    email=sender_email,
                    source="Email",
                    subject=subject,
                    body=body,
                    attachment_name=att_name,
                    attachment_data=att_data
                )
                
                ticket_processor_callback(ticket)
                tickets.append(ticket)
                
                # Copy and Move to Processed
                try:
                    result, _ = mail.copy(num, processed_folder)
                    if result == "OK":
                        mail.store(num, '+FLAGS', '\\Deleted')
                    else:
                        mail.create(processed_folder)
                        result, _ = mail.copy(num, processed_folder)
                        if result == "OK":
                            mail.store(num, '+FLAGS', '\\Deleted')
                except Exception as ex:
                    print(f"Failed to move email to processed: {ex}. Marking Seen only.")
                    mail.store(num, '+FLAGS', '\\Seen')
                    
            mail.expunge()
            mail.logout()
        except Exception as e:
            print(f"IMAP active polling error: {e}")
            raise e
            
        return tickets

    def _get_simulated_emails(self) -> List[Ticket]:
        simulated = [
            {
                "sender_name": "Alice Johnson",
                "sender": "alice.j@example.com",
                "subject": "Urgent: Billing issue - invoice incorrect",
                "body": "Hi Support team, I noticed that invoice INV-2026-9908 displays double the agreed amount of $1,250.00. Please fix this asap as our account is down."
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
