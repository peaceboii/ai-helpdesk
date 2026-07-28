import json
import os
from typing import Dict, Any

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.json')

def load_config() -> Dict[str, Any]:
    """Loads configuration parameters from config.json."""
    if not os.path.exists(CONFIG_PATH):
        return {
            "routing_rules": {
                "Billing": "Finance Team",
                "Technical": "Engineering",
                "HR": "Human Resources",
                "General": "Customer Support"
            },
            "confidence_threshold": 60.0,
            "spam_keywords": [],
            "high_priority_keywords": [],
            "department_contacts": {
                "Finance Team": "kumaravelu2003@gmail.com",
                "Engineering": "kumaravelu2003@gmail.com",
                "Human Resources": "kumaravelu2003@gmail.com",
                "Customer Support": "kumaravelu2003@gmail.com",
                "Customer Support (Escalated)": "kumaravelu2003@gmail.com",
                "Spam Folder": "kumaravelu2003@gmail.com"
            }
        }
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def save_config(config_data: Dict[str, Any]) -> None:
    """Saves configuration parameters to config.json."""
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config_data, f, indent=2)
