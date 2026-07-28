from typing import Dict, Any
from app.connectors.base import BaseConnector
from app.connectors.email_connector import EmailConnector
from app.connectors.slack_connector import SlackConnector
from app.connectors.telegram_connector import TelegramConnector
from app.connectors.whatsapp_connector import WhatsAppConnector
from app.connectors.website_connector import WebsiteConnector
from app.connectors.api_connector import APIConnector
from app.services.database_service import IntegrationRepository

class ConnectorFactory:
    @staticmethod
    def get_connector(source_type: str, config: Dict[str, Any] = None) -> BaseConnector:
        source_lower = source_type.lower()
        
        # If no config is passed, try to load it from the database settings
        if config is None:
            db_settings = {}
            if "email" in source_lower:
                db_settings = IntegrationRepository.get_settings("email").get("settings", {})
            elif "slack" in source_lower:
                db_settings = IntegrationRepository.get_settings("slack").get("settings", {})
            elif "telegram" in source_lower:
                db_settings = IntegrationRepository.get_settings("telegram").get("settings", {})
            elif "whatsapp" in source_lower:
                db_settings = IntegrationRepository.get_settings("whatsapp").get("settings", {})
            elif "web" in source_lower:
                db_settings = IntegrationRepository.get_settings("website").get("settings", {})
            elif "api" in source_lower or "rest" in source_lower:
                db_settings = IntegrationRepository.get_settings("api").get("settings", {})
            cfg = db_settings
        else:
            cfg = config

        if "email" in source_lower:
            return EmailConnector(cfg)
        elif "slack" in source_lower:
            return SlackConnector(cfg)
        elif "telegram" in source_lower:
            return TelegramConnector(cfg)
        elif "whatsapp" in source_lower:
            return WhatsAppConnector(cfg)
        elif "web" in source_lower:
            return WebsiteConnector(cfg)
        else:
            return APIConnector(cfg)
