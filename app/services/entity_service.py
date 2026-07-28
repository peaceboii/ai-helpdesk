from typing import Dict, Any
from app.services.entity_extraction_service import EntityExtractionService

class EntityService:
    @staticmethod
    def extract_entities(text: str) -> Dict[str, Any]:
        """Extracts structured entities from ticket text (delegates to EntityExtractionService)."""
        return EntityExtractionService.extract_entities(text)
