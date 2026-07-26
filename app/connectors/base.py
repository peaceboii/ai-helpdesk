from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.models.ticket import Ticket

class BaseConnector(ABC):
    @abstractmethod
    def ingest(self, payload: Dict[str, Any], attachment_name: Optional[str] = None, attachment_data: Optional[bytes] = None) -> Ticket:
        """
        Parses the raw source payload and returns a normalized Ticket object.
        """
        pass
