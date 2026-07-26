from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr
from typing import Dict, Any, Optional
from app.connectors.factory import ConnectorFactory
from app.services.ticket_processor import TicketProcessor
from app.services.database_service import TicketRepository

router = APIRouter()
processor = TicketProcessor()

# Pydantic models for API validation
class RESTTicketIn(BaseModel):
    customer_name: str
    email: EmailStr
    subject: str
    description: str
    source: Optional[str] = "REST API"

class WhatsAppWebhookIn(BaseModel):
    from_number: str
    profile_name: str
    text: str

class SlackWebhookIn(BaseModel):
    user_id: str
    user_name: str
    text: str
    channel: str

class TelegramWebhookIn(BaseModel):
    chat_id: int
    first_name: str
    username: str
    text: str

@router.post("/api/tickets")
async def create_ticket(payload: RESTTicketIn):
    try:
        # Ingest using factory
        connector = ConnectorFactory.get_connector("REST API")
        ticket = connector.ingest(payload.model_dump())
        
        # Process ticket
        res = processor.process(ticket)
        if res.get("status") == "Rejected":
            raise HTTPException(status_code=400, detail=res.get("reason"))
            
        return {
            "ticket_id": res.get("ticket_id"),
            "prediction": res.get("category"),
            "confidence": res.get("confidence"),
            "priority": res.get("priority"),
            "assigned_team": res.get("assigned_team")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook/whatsapp")
async def whatsapp_webhook(payload: WhatsAppWebhookIn):
    try:
        connector = ConnectorFactory.get_connector("WhatsApp")
        ticket = connector.ingest(payload.model_dump())
        res = processor.process(ticket)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook/slack")
async def slack_webhook(payload: SlackWebhookIn):
    try:
        connector = ConnectorFactory.get_connector("Slack")
        ticket = connector.ingest(payload.model_dump())
        res = processor.process(ticket)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook/telegram")
async def telegram_webhook(payload: TelegramWebhookIn):
    try:
        connector = ConnectorFactory.get_connector("Telegram")
        ticket = connector.ingest(payload.model_dump())
        res = processor.process(ticket)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/tickets")
async def get_tickets(search: str = "", category: str = "All", priority: str = "All", status: str = "All"):
    try:
        tickets = TicketRepository.list_tickets(search=search, category=category, priority=priority, status=status)
        return [t.to_dict() for t in tickets]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
