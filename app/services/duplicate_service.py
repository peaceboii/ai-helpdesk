import joblib
import numpy as np
import os
import sys
from typing import Tuple, Optional
from sklearn.metrics.pairwise import cosine_similarity
from app.services.database_service import TicketRepository

# Add parent directory to sys.path for importing the legacy utils helper
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils import clean_text

class DuplicateService:
    @staticmethod
    def find_duplicate(subject: str, body: str, threshold: float = 0.90) -> Tuple[bool, Optional[str], float]:
        """
        Calculates cosine similarity of new ticket text against all existing database tickets.
        Returns (is_duplicate, duplicate_ticket_id, similarity_score).
        """
        # Get all non-spam tickets
        existing_tickets = TicketRepository.list_tickets(status="All")
        if not existing_tickets:
            return False, None, 0.0
            
        # Clean current text
        new_text = clean_text(subject + " " + body)
        if not new_text:
            return False, None, 0.0
            
        # Load vectorizer
        vectorizer_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models', 'vectorizer.pkl')
        if not os.path.exists(vectorizer_path):
            # Fallback to simple set comparison if vectorizer not trained yet
            return False, None, 0.0
            
        try:
            vectorizer = joblib.load(vectorizer_path)
            
            # Vectorize new text
            new_vec = vectorizer.transform([new_text])
            
            # Vectorize all existing ticket bodies + subjects
            existing_texts = [clean_text(t.subject + " " + t.body) for t in existing_tickets]
            
            # Filter empty texts
            valid_indices = [i for i, txt in enumerate(existing_texts) if txt]
            if not valid_indices:
                return False, None, 0.0
                
            filtered_texts = [existing_texts[i] for i in valid_indices]
            existing_vecs = vectorizer.transform(filtered_texts)
            
            # Calculate similarities
            similarities = cosine_similarity(new_vec, existing_vecs)[0]
            max_idx = np.argmax(similarities)
            max_sim = similarities[max_idx]
            
            if max_sim >= threshold:
                original_ticket = existing_tickets[valid_indices[max_idx]]
                return True, original_ticket.ticket_id, float(max_sim)
                
        except Exception as e:
            print(f"Error checking duplicates: {e}")
            
        return False, None, 0.0
