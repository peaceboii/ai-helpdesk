from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime

@dataclass
class Ticket:
    ticket_id: str  # Format: SUP-YYYY-XXXXXX
    customer_name: str
    email: str
    source: str  # Email, Web Form, Slack, Telegram, WhatsApp, REST API, Manual Entry
    subject: str
    body: str
    created_time: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    status: str = "Open"  # Open, Pending, Resolved
    priority: str = "NORMAL"  # HIGH, NORMAL
    category: str = "General"  # Billing, Technical, HR, General
    confidence: float = 0.0
    language: str = "en"
    entities: Dict[str, Any] = field(default_factory=dict)
    sentiment: str = "Neutral"  # Positive, Neutral, Negative, Very Angry
    is_spam: bool = False
    original_body: Optional[str] = None
    assigned_team: Optional[str] = None  # Finance Team, Engineering, Human Resources, Customer Support
    merged_with: Optional[str] = None  # Ticket ID if merged
    attachment_name: Optional[str] = None
    attachment_data: Optional[bytes] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticket_id": self.ticket_id,
            "customer_name": self.customer_name,
            "email": self.email,
            "source": self.source,
            "subject": self.subject,
            "body": self.body,
            "created_time": self.created_time,
            "status": self.status,
            "priority": self.priority,
            "category": self.category,
            "confidence": self.confidence,
            "language": self.language,
            "entities": self.entities,
            "sentiment": self.sentiment,
            "is_spam": self.is_spam,
            "original_body": self.original_body,
            "assigned_team": self.assigned_team,
            "merged_with": self.merged_with,
            "attachment_name": self.attachment_name
        }
