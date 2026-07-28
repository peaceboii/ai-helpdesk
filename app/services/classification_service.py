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
            return "General", 50.0, {"Billing": 25.0, "Technical": 25.0, "HR": 25.0, "General": 50.0}
            
        vec = self.vectorizer.transform([cleaned])
        probs = self.classifier.predict_proba(vec)[0]
        classes = self.classifier.classes_
        
        max_idx = np.argmax(probs)
        predicted_class = classes[max_idx]
        confidence = float(probs[max_idx]) * 100
        
        prob_dict = {cls: float(prob) * 100 for cls, prob in zip(classes, probs)}
        
        return predicted_class, confidence, prob_dict
