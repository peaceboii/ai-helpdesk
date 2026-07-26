from typing import List
from app.utils.config import load_config

class SpamService:
    @staticmethod
    def is_spam(subject: str, body: str) -> bool:
        """
        Detects if a ticket is spam based on:
        - Empty content
        - Blocklisted spam keywords from config
        """
        combined = (subject + " " + body).lower().strip()
        
        # 1. Check if empty
        if not combined:
            return True
            
        # 2. Check spam keywords
        config = load_config()
        spam_keywords = config.get("spam_keywords", [])
        
        for kw in spam_keywords:
            if kw.lower() in combined:
                return True
                
        # 3. Basic heuristic for marketing ads
        if "make money online" in combined or "seo services" in combined:
            return True
            
        return False
