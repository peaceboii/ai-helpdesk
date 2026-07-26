import sys
import os
import importlib.util

# Manually load the 'app/' package and register it in sys.modules
# to prevent filename collisions.
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.join(current_dir, 'app')
init_file = os.path.join(app_dir, '__init__.py')

spec = importlib.util.spec_from_file_location('app', init_file)
app_module = importlib.util.module_from_spec(spec)
app_module.__path__ = [app_dir]
sys.modules['app'] = app_module
spec.loader.exec_module(app_module)

from app.services.classification_service import ClassificationService
from utils import detect_priority
from app.utils.config import load_config

def predict_ticket(subject: str, body: str) -> dict:
    """
    Predicts the category of a support ticket given the subject and body.
    Implements confidence thresholding and priority detection.
    Preserves exact original signature for backward compatibility.
    """
    classifier = ClassificationService()
    predicted_class, confidence, probs = classifier.predict(subject, body)
    
    combined_text = subject + " " + body
    priority = detect_priority(combined_text)
    
    config = load_config()
    threshold = config.get("confidence_threshold", 60.0)
    
    if confidence < threshold:
        predicted_category = "Needs Human Review"
    else:
        predicted_category = predicted_class
        
    return {
        "Predicted Category": predicted_category,
        "Original Prediction": predicted_class,
        "Confidence %": confidence,
        "Priority": priority,
        "Probabilities": probs
    }

def main():
    print("=== Support Ticket Categorizer ===")
    try:
        subject = input("Subject:\n> ")
        body = input("Body:\n> ")
    except EOFError:
        return
        
    print("\n--- Processing ---")
    result = predict_ticket(subject, body)
    
    print(f"\nPredicted Category: {result['Predicted Category']}")
    print(f"Confidence: {result['Confidence %']:.2f}%")
    print(f"Priority: {result['Priority']}")
    
    print("\nProbability of every class:")
    for cls, prob in result['Probabilities'].items():
        print(f" - {cls}: {prob:.2f}%")

if __name__ == '__main__':
    main()
