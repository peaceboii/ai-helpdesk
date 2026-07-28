import smtplib
from email.mime.text import MIMEText
import requests
import json
from typing import Dict, Any, Optional
from app.models.ticket import Ticket
from app.services.database_service import IntegrationRepository

class NotificationService:
    @staticmethod
    def send_auto_acknowledgement(ticket: Ticket, auto_response_text: str) -> bool:
        """
        Sends the auto-acknowledgment message back to the customer on their ingestion channel.
        """
        source = ticket.source.lower()
        
        if "email" in source:
            return NotificationService._send_email_ack(ticket, auto_response_text)
        elif "telegram" in source:
            return NotificationService._send_telegram_ack(ticket, auto_response_text)
        elif "slack" in source:
            return NotificationService._send_slack_ack(ticket, auto_response_text)
        elif "whatsapp" in source:
            return NotificationService._send_whatsapp_ack(ticket, auto_response_text)
        else:
            # For REST API, Website or Manual, we log it
            channel_id = "website" if "web" in source else "api"
            IntegrationRepository.update_logs(
                channel_id,
                add_log_message=f"Auto-ack logged for ticket {ticket.ticket_id}: Sent to {ticket.email}"
            )
            return True

    @staticmethod
    def _send_email_ack(ticket: Ticket, body: str) -> bool:
        # Load email integration settings
        res = IntegrationRepository.get_settings("email")
        cfg = res.get("settings", {})
        if not res.get("enabled") or not cfg.get("email_address") or not cfg.get("app_password"):
            IntegrationRepository.update_logs("email", add_log_message=f"Simulated email acknowledgment for ticket {ticket.ticket_id} sent to {ticket.email}")
            return True
            
        try:
            imap_host = cfg.get("imap_host", "")
            smtp_host = "smtp.gmail.com"
            if "outlook" in imap_host.lower() or "office365" in imap_host.lower():
                smtp_host = "smtp.office365.com"
            elif "gmail" in imap_host.lower():
                smtp_host = "smtp.gmail.com"
            else:
                smtp_host = imap_host.replace("imap", "smtp")
                
            sender = cfg.get("email_address")
            password = cfg.get("app_password")
            
            msg = MIMEText(body)
            msg["Subject"] = f"Re: {ticket.subject} [Ticket: {ticket.ticket_id}]"
            msg["From"] = sender
            msg["To"] = ticket.email
            
            try:
                server = smtplib.SMTP_SSL(smtp_host, 465, timeout=10)
                server.login(sender, password)
            except Exception:
                server = smtplib.SMTP(smtp_host, 587, timeout=10)
                server.starttls()
                server.login(sender, password)
                
            server.send_message(msg)
            server.quit()
            IntegrationRepository.update_logs("email", add_log_message=f"Email acknowledgment sent successfully to {ticket.email} for ticket {ticket.ticket_id}")
            return True
        except Exception as e:
            err_msg = f"Failed to send email acknowledgment: {e}"
            IntegrationRepository.update_logs("email", increment_errors=True, add_log_message=err_msg)
            return False

    @staticmethod
    def _send_telegram_ack(ticket: Ticket, body: str) -> bool:
        res = IntegrationRepository.get_settings("telegram")
        cfg = res.get("settings", {})
        bot_token = cfg.get("bot_token")
        
        chat_id = ticket.entities.get("Telegram Chat ID")
        if not chat_id:
            chat_id = ticket.email.split("@")[0]
            
        if not res.get("enabled") or not bot_token or not chat_id:
            IntegrationRepository.update_logs("telegram", add_log_message=f"Simulated Telegram acknowledgment for ticket {ticket.ticket_id} to Chat {chat_id}")
            return True
            
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": body
            }
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                IntegrationRepository.update_logs("telegram", add_log_message=f"Telegram acknowledgment sent successfully to chat {chat_id} for ticket {ticket.ticket_id}")
                return True
            else:
                raise Exception(f"Telegram API status {resp.status_code}: {resp.text}")
        except Exception as e:
            err_msg = f"Failed to send Telegram acknowledgment: {e}"
            IntegrationRepository.update_logs("telegram", increment_errors=True, add_log_message=err_msg)
            return False

    @staticmethod
    def _send_slack_ack(ticket: Ticket, body: str) -> bool:
        res = IntegrationRepository.get_settings("slack")
        cfg = res.get("settings", {})
        bot_token = cfg.get("bot_token")
        channel = ticket.entities.get("Slack Channel ID") or cfg.get("allowed_channels", "").split(",")[0].strip()
        thread_ts = ticket.entities.get("Slack Thread TS")
        
        if not res.get("enabled") or not bot_token or not channel:
            IntegrationRepository.update_logs("slack", add_log_message=f"Simulated Slack acknowledgment for ticket {ticket.ticket_id} to Channel {channel}")
            return True
            
        try:
            url = "https://slack.com/api/chat.postMessage"
            headers = {
                "Authorization": f"Bearer {bot_token}",
                "Content-Type": "application/json"
            }
            payload = {
                "channel": channel,
                "text": body
            }
            if thread_ts:
                payload["thread_ts"] = thread_ts
                
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            resp_data = resp.json()
            if resp.status_code == 200 and resp_data.get("ok"):
                IntegrationRepository.update_logs("slack", add_log_message=f"Slack acknowledgment sent successfully to channel {channel} for ticket {ticket.ticket_id}")
                return True
            else:
                raise Exception(f"Slack API error: {resp_data.get('error') or resp.text}")
        except Exception as e:
            err_msg = f"Failed to send Slack acknowledgment: {e}"
            IntegrationRepository.update_logs("slack", increment_errors=True, add_log_message=err_msg)
            return False

    @staticmethod
    def _send_whatsapp_ack(ticket: Ticket, body: str) -> bool:
        res = IntegrationRepository.get_settings("whatsapp")
        cfg = res.get("settings", {})
        phone_id = cfg.get("phone_number_id")
        access_token = cfg.get("access_token")
        
        to_phone = ticket.entities.get("Phone")
        if not to_phone:
            to_phone = ticket.email.split("@")[0]
            
        if not res.get("enabled") or not phone_id or not access_token or not to_phone:
            IntegrationRepository.update_logs("whatsapp", add_log_message=f"Simulated WhatsApp acknowledgment for ticket {ticket.ticket_id} to {to_phone}")
            return True
            
        try:
            url = f"https://graph.facebook.com/v17.0/{phone_id}/messages"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            payload = {
                "messaging_product": "whatsapp",
                "to": to_phone,
                "type": "text",
                "text": {
                    "body": body
                }
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            resp_data = resp.json()
            if resp.status_code == 200 or resp_data.get("messages"):
                IntegrationRepository.update_logs("whatsapp", add_log_message=f"WhatsApp acknowledgment sent successfully to {to_phone} for ticket {ticket.ticket_id}")
                return True
            else:
                raise Exception(f"WhatsApp API error: {resp_data.get('error', {}).get('message') or resp.text}")
        except Exception as e:
            err_msg = f"Failed to send WhatsApp acknowledgment: {e}"
            IntegrationRepository.update_logs("whatsapp", increment_errors=True, add_log_message=err_msg)
            return False

    @staticmethod
    def notify_department(ticket: Ticket, subject: str, body: str) -> None:
        """Forwards ticket details and customer communication copies to the assigned department contact."""
        from app.utils.config import load_config
        config = load_config()
        contacts = config.get("department_contacts", {})
        
        team = ticket.assigned_team or "Customer Support"
        recipient = contacts.get(team, "kumaravelu2003@gmail.com")
        if not recipient:
            recipient = "kumaravelu2003@gmail.com"
            
        res = IntegrationRepository.get_settings("email")
        cfg = res.get("settings", {})
        if not res.get("enabled") or not cfg.get("email_address") or not cfg.get("app_password"):
            # Fallback mock logging if IMAP/SMTP credentials are not yet configured
            IntegrationRepository.update_logs("email", add_log_message=f"Department forward (Mock): Ticket {ticket.ticket_id} details copy routed to {recipient}")
            return
            
        try:
            import smtplib
            from email.mime.text import MIMEText
            
            imap_host = cfg.get("imap_host", "")
            smtp_host = "smtp.gmail.com"
            if "outlook" in imap_host.lower() or "office365" in imap_host.lower():
                smtp_host = "smtp.office365.com"
            elif "gmail" in imap_host.lower():
                smtp_host = "smtp.gmail.com"
            else:
                smtp_host = imap_host.replace("imap", "smtp")
                
            sender = cfg.get("email_address")
            password = cfg.get("app_password")
            
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = sender
            msg["To"] = recipient
            
            try:
                server = smtplib.SMTP_SSL(smtp_host, 465, timeout=10)
                server.login(sender, password)
            except Exception:
                server = smtplib.SMTP(smtp_host, 587, timeout=10)
                server.starttls()
                server.login(sender, password)
                
            server.send_message(msg)
            server.quit()
            IntegrationRepository.update_logs("email", add_log_message=f"Department forward: Successfully routed notification to {recipient} for ticket {ticket.ticket_id}")
        except Exception as e:
            err_msg = f"Failed to forward ticket notification to department ({recipient}): {e}"
            IntegrationRepository.update_logs("email", increment_errors=True, add_log_message=err_msg)
