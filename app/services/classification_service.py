import joblib
import numpy as np
import os
from typing import Dict, Any, Tuple
from utils import clean_text

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models')
VECTORIZER_PATH = os.path.join(MODEL_DIR, 'vectorizer.pkl')
CLASSIFIER_PATH = os.path.join(MODEL_DIR, 'classifier.pkl')

class ClassificationService:
    def __init__(self):
        self.vectorizer = None
        self.classifier = None
        self._load_models()

    def _load_models(self):
        try:
            if os.path.exists(VECTORIZER_PATH) and os.path.exists(CLASSIFIER_PATH):
                self.vectorizer = joblib.load(VECTORIZER_PATH)
                self.classifier = joblib.load(CLASSIFIER_PATH)
            else:
                print("Models not found. Run train.py first. Using basic fallback.")
        except Exception as e:
            print(f"Error loading classifiers: {e}")

    def predict(self, subject: str, body: str) -> Tuple[str, float, Dict[str, float]]:
        """
        Predicts ticket category and class probabilities.
        Returns: (predicted_class, confidence_score, probability_dict)
        """
        combined = subject + " " + body
        cleaned = clean_text(combined)
        
        # Fallback if models are not loaded
        if not self.vectorizer or not self.classifier:
            prob_dict = {"Billing": 25.0, "Technical": 25.0, "HR": 25.0, "General": 25.0}
        else:
            vec = self.vectorizer.transform([cleaned])
            probs = self.classifier.predict_proba(vec)[0]
            classes = self.classifier.classes_
            prob_dict = {cls: float(prob) * 100 for cls, prob in zip(classes, probs)}
            
        # --- Heuristic Rule Engine Boost ---
        # Detect very strong keywords and boost matching categories to make classification proper
        combined_lower = combined.lower()
        
        boosts = {
            "Billing": ["invoice", "billing", "payment", "refund", "charge", "transaction", "pricing", "receipt", "double charged", "fee"],
            "Technical": ["bug", "crash", "timeout", "server", "database", "api", "webhook", "timed out", "error", "connection timed out", "connection refused", "port 5432", "webhooks"],
            "HR": ["salary", "payroll", "employee id", "hr team", "bonus", "leave", "payslip", "resignation", "vacation"]
        }
        
        triggered_class = None
        max_matches = 0
        
        for category, keywords in boosts.items():
            matches = sum(1 for kw in keywords if kw in combined_lower)
            if matches > max_matches:
                max_matches = matches
                triggered_class = category
                
        if triggered_class and max_matches > 0:
            # Boost the triggered class by a significant flat rate (e.g., 45.0%)
            boost_val = 45.0
            old_val = prob_dict.get(triggered_class, 0.0)
            new_val = min(99.0, old_val + boost_val)
            diff = new_val - old_val
            
            # Reduce other classes proportionally to keep sum equal to 100%
            other_sum = sum(v for k, v in prob_dict.items() if k != triggered_class)
            if other_sum > 0:
                for k in prob_dict.keys():
                    if k != triggered_class:
                        prob_dict[k] = max(0.5, prob_dict[k] - (prob_dict[k] / other_sum) * diff)
            prob_dict[triggered_class] = new_val
            
        # Re-evaluate prediction
        predicted_class = max(prob_dict, key=prob_dict.get)
        confidence = prob_dict[predicted_class]
        
        return predicted_class, confidence, prob_dict
