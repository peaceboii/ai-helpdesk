import requests
from typing import Dict, Any, Optional
from datetime import datetime
from app.connectors.base import BaseConnector
from app.models.ticket import Ticket
from app.services.database_service import TicketRepository

class SlackConnector(BaseConnector):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.bot_token = config.get("bot_token", "")
        self.signing_secret = config.get("signing_secret", "")
        self.app_token = config.get("app_token", "")
        self.workspace_name = config.get("workspace_name", "")
        self.allowed_channels = [c.strip() for c in config.get("allowed_channels", "").split(",") if c.strip()]

    def ingest(self, payload: Dict[str, Any], attachment_name: Optional[str] = None, attachment_data: Optional[bytes] = None) -> Ticket:
        """
        Parses Slack webhook event payload.
        Expected keys: user_id, user_name, text, channel, ts
        """
        ticket_id = TicketRepository.get_next_ticket_id()
        user_name = payload.get("user_name", "Slack User")
        user_id = payload.get("user_id", "Unknown")
        text = payload.get("text", "")
        channel = payload.get("channel", "")
        ts = payload.get("ts", "")
        
        # Split text into subject (first line) and body (rest)
        lines = text.split("\n", 1)
        subject = lines[0] if lines else "Slack Ticket"
        if len(subject) > 60:
            subject = subject[:57] + "..."
        body = lines[1] if len(lines) > 1 else text
        
        ticket = Ticket(
            ticket_id=ticket_id,
            customer_name=user_name,
            email=f"{user_id}@slack.com",
            source="Slack",
            subject=subject,
            body=body,
            attachment_name=attachment_name,
            attachment_data=attachment_data
        )
        
        # Store routing info in entities
        ticket.entities["Slack Channel ID"] = channel
        ticket.entities["Slack Thread TS"] = ts
        
        return ticket

    def test_connection(self) -> str:
        """
        Tests connection to Slack using auth.test endpoint.
        Returns: 'Connected', 'Invalid Token', or 'Disconnected'
        """
        if not self.bot_token:
            return "Disconnected"
            
        if self.bot_token == "mock_token":
            return "Connected"
            
        try:
            url = "https://slack.com/api/auth.test"
            headers = {
                "Authorization": f"Bearer {self.bot_token}"
            }
            resp = requests.post(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    return "Connected"
                else:
                    err = data.get("error", "")
                    if err in ["invalid_auth", "token_revoked", "account_inactive"]:
                        return "Invalid Token"
            elif resp.status_code in [401, 403]:
                return "Invalid Token"
            return "Disconnected"
        except Exception as e:
            print(f"Slack connection testing error: {e}")
            return "Disconnected"

    def download_file(self, download_url: str) -> Optional[bytes]:
        """
        Downloads a private file from Slack using Bot Token auth.
        """
        if not self.bot_token or self.bot_token == "mock_token":
            return b"Simulated slack file bytes content."
            
        try:
            headers = {
                "Authorization": f"Bearer {self.bot_token}"
            }
            resp = requests.get(download_url, headers=headers, timeout=20)
            if resp.status_code == 200:
                return resp.content
        except Exception as e:
            print(f"Slack file download error: {e}")
        return None
