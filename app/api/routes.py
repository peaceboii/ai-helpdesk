from fastapi import APIRouter, HTTPException, Request, Form, UploadFile, File
from pydantic import BaseModel, EmailStr
from typing import Dict, Any, Optional
import json

from app.connectors.factory import ConnectorFactory
from app.services.ticket_service import TicketService
from app.services.database_service import TicketRepository, IntegrationRepository

router = APIRouter()
ticket_service = TicketService()

# Existing Pydantic models for legacy API support
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

# 1. API Ingestion Endpoint: POST /tickets
@router.post("/tickets")
@router.post("/api/tickets")
async def create_ticket(payload: RESTTicketIn):
    try:
        connector = ConnectorFactory.get_connector("REST API")
        ticket = connector.ingest(payload.model_dump())
        res = ticket_service.process_incoming_ticket(ticket)
        if res.get("status") == "Rejected":
            raise HTTPException(status_code=400, detail=res.get("reason"))
        return res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. Email Webhook Ingestion: POST /webhook/email
@router.post("/webhook/email")
async def email_webhook(payload: Dict[str, Any]):
    try:
        connector = ConnectorFactory.get_connector("Email")
        ticket = connector.ingest(payload)
        res = ticket_service.process_incoming_ticket(ticket)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 3. Telegram Webhook Ingestion: POST /webhook/telegram
@router.post("/webhook/telegram")
async def telegram_webhook(payload: Dict[str, Any]):
    try:
        connector = ConnectorFactory.get_connector("Telegram")
        
        # Check if it's a real Telegram bot event or a simulated payload
        if "message" in payload:
            message = payload["message"]
            chat_id = message.get("chat", {}).get("id")
            from_user = message.get("from", {})
            first_name = from_user.get("first_name", "Telegram User")
            username = from_user.get("username", "unknown")
            
            text = message.get("text", "")
            caption = message.get("caption", "")
            if caption and not text:
                text = caption
                
            attachment_name = None
            attachment_data = None
            
            # Support Photo, Document, Voice download
            if "photo" in message:
                photo_list = message["photo"]
                largest_photo = photo_list[-1]
                file_id = largest_photo["file_id"]
                attachment_name = f"photo_{file_id}.jpg"
                attachment_data = connector.download_file(file_id)
            elif "document" in message:
                doc = message["document"]
                file_id = doc["file_id"]
                attachment_name = doc.get("file_name", f"doc_{file_id}")
                attachment_data = connector.download_file(file_id)
            elif "voice" in message:
                voice = message["voice"]
                file_id = voice["file_id"]
                attachment_name = f"voice_{file_id}.ogg"
                attachment_data = connector.download_file(file_id)
                
            ingest_payload = {
                "chat_id": chat_id,
                "first_name": first_name,
                "username": username,
                "text": text or "Empty Telegram message"
            }
            ticket = connector.ingest(ingest_payload, attachment_name, attachment_data)
            res = ticket_service.process_incoming_ticket(ticket)
            return res
        else:
            # Fallback for simple tests / legacy schema
            ticket = connector.ingest(payload)
            res = ticket_service.process_incoming_ticket(ticket)
            return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 4. Slack Webhook Ingestion: POST /webhook/slack
@router.post("/webhook/slack")
async def slack_webhook(payload: Dict[str, Any]):
    try:
        # Handle Slack URL verification challenge
        if payload.get("type") == "url_verification":
            return {"challenge": payload.get("challenge")}
            
        connector = ConnectorFactory.get_connector("Slack")
        
        if "event" in payload:
            event = payload["event"]
            if event.get("bot_id") or event.get("subtype") == "bot_message":
                return {"status": "ignored", "reason": "Bot messages ignored."}
                
            user_id = event.get("user", "Unknown")
            text = event.get("text", "")
            channel = event.get("channel", "")
            ts = event.get("ts", "")
            
            attachment_name = None
            attachment_data = None
            
            if "files" in event and event["files"]:
                first_file = event["files"][0]
                attachment_name = first_file.get("name")
                download_url = first_file.get("url_private")
                if download_url:
                    attachment_data = connector.download_file(download_url)
                    
            ingest_payload = {
                "user_id": user_id,
                "user_name": user_id,
                "text": text,
                "channel": channel,
                "ts": ts
            }
            ticket = connector.ingest(ingest_payload, attachment_name, attachment_data)
            res = ticket_service.process_incoming_ticket(ticket)
            return res
        else:
            # Fallback for simple test payloads
            ticket = connector.ingest(payload)
            res = ticket_service.process_incoming_ticket(ticket)
            return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 5. Meta WhatsApp Webhook Ingestion: GET (verify challenge) & POST (payload entry)
@router.get("/webhook/whatsapp")
async def whatsapp_get_verification(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    
    settings_res = IntegrationRepository.get_settings("whatsapp")
    db_token = settings_res.get("settings", {}).get("verify_token") or "mock_verify_token"
    
    if mode and token:
        if mode == "subscribe" and token == db_token:
            from fastapi.responses import PlainTextResponse
            return PlainTextResponse(content=challenge)
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/webhook/whatsapp")
async def whatsapp_post_webhook(payload: Dict[str, Any]):
    try:
        connector = ConnectorFactory.get_connector("WhatsApp")
        
        if "entry" in payload:
            for entry in payload.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    if "messages" in value:
                        for msg in value.get("messages", []):
                            from_number = msg.get("from")
                            profile_name = value.get("contacts", [{}])[0].get("profile", {}).get("name", "WhatsApp User")
                            
                            text = ""
                            attachment_name = None
                            attachment_data = None
                            
                            msg_type = msg.get("type")
                            if msg_type == "text":
                                text = msg.get("text", {}).get("body", "")
                            elif msg_type == "image":
                                image = msg.get("image", {})
                                media_id = image.get("id")
                                attachment_name = f"image_{media_id}.jpg"
                                attachment_data = connector.download_media(media_id)
                                text = msg.get("image", {}).get("caption", "WhatsApp Image")
                            elif msg_type == "document":
                                doc = msg.get("document", {})
                                media_id = doc.get("id")
                                attachment_name = doc.get("filename", f"document_{media_id}")
                                attachment_data = connector.download_media(media_id)
                                text = doc.get("caption", "WhatsApp Document")
                            elif msg_type == "voice":
                                voice = msg.get("voice", {})
                                media_id = voice.get("id")
                                attachment_name = f"voice_{media_id}.ogg"
                                attachment_data = connector.download_media(media_id)
                                text = "WhatsApp Voice Note"
                                
                            ingest_payload = {
                                "from_number": from_number,
                                "profile_name": profile_name,
                                "text": text or "WhatsApp Message"
                              }
                            ticket = connector.ingest(ingest_payload, attachment_name, attachment_data)
                            res = ticket_service.process_incoming_ticket(ticket)
                            return res
            return {"status": "ignored", "reason": "No entry message change."}
        else:
            # Fallback for simple tests
            ticket = connector.ingest(payload)
            res = ticket_service.process_incoming_ticket(ticket)
            return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 6. Website Ingest Form Submission: POST /webhook/website
@router.post("/webhook/website")
async def website_webhook(
    payload: str = Form(...),
    attachment: Optional[UploadFile] = File(None)
):
    try:
        payload_dict = json.loads(payload)
        connector = ConnectorFactory.get_connector("Website")
        
        att_name = None
        att_data = None
        if attachment:
            att_name = attachment.filename
            att_data = await attachment.read()
            
        ticket = connector.ingest(payload_dict, att_name, att_data)
        res = ticket_service.process_incoming_ticket(ticket)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Existing list endpoint
@router.get("/api/tickets")
async def get_tickets(search: str = "", category: str = "All", priority: str = "All", status: str = "All"):
    try:
        tickets = TicketRepository.list_tickets(search=search, category=category, priority=priority, status=status)
        return [t.to_dict() for t in tickets]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
