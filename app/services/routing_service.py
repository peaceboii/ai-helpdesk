from typing import Dict, Any
from app.utils.config import load_config

class RoutingService:
    @staticmethod
    def get_assigned_team(category: str) -> str:
        """
        Maps a category to its designated department team.
        Looks up rules from config.json.
        """
        config = load_config()
        routing_rules = config.get("routing_rules", {
            "Billing": "Finance Team",
            "Technical": "Engineering",
            "HR": "Human Resources",
            "General": "Customer Support"
        })
        
        # In case the category is "Needs Human Review"
        if category == "Needs Human Review":
            return "Customer Support (Escalated)"
            
        return routing_rules.get(category, "Customer Support")
