from datetime import datetime
import re
import os
import sys
from typing import Dict, Any, Tuple
from langdetect import detect as detect_lang

from app.models.ticket import Ticket
from app.services.database_service import TicketRepository
from app.services.ocr_service import OCRService
from app.services.spam_service import SpamService
from app.services.duplicate_service import DuplicateService
from app.services.entity_extraction_service import EntityExtractionService
from app.services.sentiment_service import SentimentService
from app.services.classification_service import ClassificationService
from app.services.routing_service import RoutingService
from app.utils.config import load_config

# Add root directory to sys.path for importing the legacy utils helper
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils import detect_priority

class TicketProcessor:
    def __init__(self):
        self.classifier = ClassificationService()

    def validate_ticket(self, ticket: Ticket) -> Tuple[bool, str]:
        """
        Validates the ticket object.
        Returns: (is_valid, error_message)
        """
        if not ticket.customer_name or not ticket.customer_name.strip():
            return False, "Customer Name is required."
            
        if not ticket.email or not ticket.email.strip():
            return False, "Email is required."
            
        # Basic Email Regex
        if not re.match(r"[^@]+@[^@]+\.[^@]+", ticket.email):
            return False, "Invalid email address format."
            
        if not ticket.subject.strip() and not ticket.body.strip():
            return False, "Subject or Body must be provided."
            
        # Check attachment size if simulated
        if ticket.attachment_data and len(ticket.attachment_data) > 10 * 1024 * 1024:  # 10MB limit
            return False, "Attachment exceeds maximum size of 10MB."
            
        return True, ""

    def process(self, ticket: Ticket) -> Dict[str, Any]:
        """
        Orchestrates the entire Helpdesk Pipeline (Modules 2 to 10).
        Saves the processed ticket to the database and returns a summary.
        """
        # 1. Validation
        is_valid, err_msg = self.validate_ticket(ticket)
        if not is_valid:
            return {"status": "Rejected", "reason": err_msg}

        # Store original body
        ticket.original_body = ticket.body
        
        # 2. Attachment OCR Processing (Module 8)
        ocr_text = ""
        if ticket.attachment_name and ticket.attachment_data:
            ocr_text = OCRService.extract_text(ticket.attachment_name, ticket.attachment_data)
            if ocr_text:
                ticket.body += f"\n\n--- Attachment Extracted Text ---\n{ocr_text}"

        # 3. Spam Detection (Module 4)
        if SpamService.is_spam(ticket.subject, ticket.body):
            ticket.is_spam = True
            ticket.status = "Spam"
            ticket.category = "General"
            ticket.assigned_team = "Spam Folder"
            TicketRepository.save_ticket(ticket)
            return {"status": "Spam", "ticket_id": ticket.ticket_id}

        # 4. Language Detection & Translation (Module 5)
        combined_text = ticket.subject + " " + ticket.body
        try:
            detected = detect_lang(combined_text)
            ticket.language = detected
        except Exception:
            ticket.language = "en"
            
        if ticket.language != "en":
            # Simulate machine translation
            ticket.body = f"[Translated from {ticket.language.upper()}]: " + ticket.body

        # 5. Duplicate Detection (Module 3)
        # Check for similarity against existing non-spam tickets
        is_duplicate, duplicate_id, similarity = DuplicateService.find_duplicate(ticket.subject, ticket.body)
        if is_duplicate:
            ticket.status = "Pending"  # Requires agent verification/merge
            ticket.merged_with = duplicate_id
            
        # 6. Entity Extraction (Module 6)
        ticket.entities = EntityExtractionService.extract_entities(combined_text)

        # 7. Sentiment Analysis (Module 7)
        ticket.sentiment = SentimentService.analyze_sentiment(combined_text)

        # 8. AI Categorization & Confidence (Module 1, 6)
        predicted_class, confidence, probabilities = self.classifier.predict(ticket.subject, ticket.body)
        ticket.confidence = confidence
        
        config = load_config()
        threshold = config.get("confidence_threshold", 60.0)
        
        if confidence < threshold:
            ticket.category = "Needs Human Review"
        else:
            ticket.category = predicted_class

        # Save probability distribution for analysis/dashboard view
        TicketRepository.save_prediction(ticket.ticket_id, predicted_class, confidence, probabilities)

        # 9. Priority Detection
        # Check base keywords + escalate if sentiment is Very Angry
        base_priority = detect_priority(combined_text)
        if ticket.sentiment == "Very Angry":
            ticket.priority = "HIGH"
        else:
            ticket.priority = base_priority

        # 10. Routing Engine (Module 9)
        ticket.assigned_team = RoutingService.get_assigned_team(ticket.category)

        # Save to database (Repository Pattern)
        TicketRepository.save_ticket(ticket)

        # 11. Auto-Response (Module 10)
        auto_response = self.generate_auto_response(ticket)

        return {
            "status": "Processed",
            "ticket_id": ticket.ticket_id,
            "category": ticket.category,
            "confidence": ticket.confidence,
            "priority": ticket.priority,
            "assigned_team": ticket.assigned_team,
            "sentiment": ticket.sentiment,
            "is_duplicate": is_duplicate,
            "duplicate_of": duplicate_id,
            "auto_response": auto_response
        }

    def generate_auto_response(self, ticket: Ticket) -> str:
        """Generates acknowledgment message based on ticket processing results."""
        eta = "24 Hours"
        if ticket.priority == "HIGH":
            eta = "4 Hours"
            
        if ticket.category == "Needs Human Review":
            cat_display = "Customer Support Queue (Manual Assignment)"
        else:
            cat_display = ticket.category

        response = (
            f"Hello {ticket.customer_name},\n\n"
            f"Your ticket has been created successfully.\n\n"
            f"Ticket ID: {ticket.ticket_id}\n"
            f"Category: {cat_display}\n"
            f"Priority: {ticket.priority}\n"
            f"Assigned Team: {ticket.assigned_team}\n"
            f"Estimated Response Time: {eta}\n\n"
            f"Thank you for contacting us.\n"
            f"AI Helpdesk Automation Platform"
        )
        return response
