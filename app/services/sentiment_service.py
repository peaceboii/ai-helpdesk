class SentimentService:
    @staticmethod
    def analyze_sentiment(text: str) -> str:
        """
        Performs sentiment analysis on ticket text.
        Returns: Positive, Neutral, Negative, or Very Angry
        """
        text_lower = text.lower()
        
        # Keywords
        very_angry_keywords = ["furious", "unacceptable", "terrible", "worst service", "very angry", "lawyer", "sue", "legal action", "disaster"]
        negative_keywords = ["disappointed", "fail", "broken", "issue", "bug", "error", "problem", "not working", "useless", "annoyed", "delay", "poor"]
        positive_keywords = ["thanks", "thank you", "great", "awesome", "happy", "perfect", "good", "satisfied", "helpful", "love"]
        
        # Scored count
        very_angry_score = sum(1 for kw in very_angry_keywords if kw in text_lower)
        negative_score = sum(1 for kw in negative_keywords if kw in text_lower)
        positive_score = sum(1 for kw in positive_keywords if kw in text_lower)
        
        # Heuristics
        # If uppercase exclamation is present and they're talking about issues
        if ("!" in text and text.isupper()) or very_angry_score > 0:
            return "Very Angry"
        elif negative_score > positive_score:
            # If negative keywords outweigh positive keywords
            if negative_score >= 3:
                return "Very Angry"
            return "Negative"
        elif positive_score > negative_score:
            return "Positive"
        else:
            return "Neutral"
