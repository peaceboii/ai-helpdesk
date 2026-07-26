from typing import Dict, Any
from app.connectors.base import BaseConnector
from app.connectors.email_connector import EmailConnector
from app.connectors.slack_connector import SlackConnector
from app.connectors.telegram_connector import TelegramConnector
from app.connectors.whatsapp_connector import WhatsAppConnector
from app.connectors.rest_connector import RESTConnector

class ConnectorFactory:
    @staticmethod
    def get_connector(source_type: str, config: Dict[str, Any] = None) -> BaseConnector:
        source_lower = source_type.lower()
        cfg = config or {}
        
        if "email" in source_lower:
            return EmailConnector(cfg.get("email_imap_config", {}))
        elif "slack" in source_lower:
            return SlackConnector()
        elif "telegram" in source_lower:
            return TelegramConnector()
        elif "whatsapp" in source_lower:
            return WhatsAppConnector()
        else:
            # Default to REST Connector for general manual or API inputs
            return RESTConnector()
