import pandas as pd
import numpy as np
import os
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report, confusion_matrix
from utils import clean_text

def plot_confusion_matrix(cm, classes, title, filename):
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=classes, yticklabels=classes)
    plt.title(title)
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

def main():
    print("Loading data...")
    train_df = pd.read_csv('data/train.csv')
    test_df = pd.read_csv('data/test.csv')
    
    # Fill NA just in case
    train_df.fillna('', inplace=True)
    test_df.fillna('', inplace=True)
    
    print("Preprocessing text...")
    # Combine subject and body
    train_df['Combined'] = train_df['Subject'] + " " + train_df['Body']
    test_df['Combined'] = test_df['Subject'] + " " + test_df['Body']
    
    # Apply text cleaning
    train_df['Cleaned'] = train_df['Combined'].apply(clean_text)
    test_df['Cleaned'] = test_df['Combined'].apply(clean_text)
    
    X_train = train_df['Cleaned']
    y_train = train_df['Category']
    X_test = test_df['Cleaned']
    y_test = test_df['Category']
    
    print("Vectorizing data with TF-IDF...")
    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1,2), min_df=2)
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    
    # Define models
    models = {
        'Naive Bayes': MultinomialNB(),
        'Logistic Regression': LogisticRegression(random_state=42, max_iter=1000)
    }
    
    results = {}
    best_model_name = None
    best_f1 = -1
    best_model = None
    
    print("Training models...")
    for name, model in models.items():
        model.fit(X_train_vec, y_train)
        y_pred = model.predict(X_test_vec)
        
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, average='weighted', zero_division=0)
        rec = recall_score(y_test, y_pred, average='weighted', zero_division=0)
        f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
        
        results[name] = {'Accuracy': acc, 'Precision': prec, 'Recall': rec, 'F1-score': f1}
        
        print(f"\n--- {name} ---")
        print(f"Accuracy: {acc:.4f}")
        print(f"Precision: {prec:.4f}")
        print(f"Recall: {rec:.4f}")
        print(f"F1-score: {f1:.4f}")
        print("\nClassification Report:\n", classification_report(y_test, y_pred, zero_division=0))
        
        # Save confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        plot_confusion_matrix(cm, model.classes_, f"Confusion Matrix - {name}", f"models/cm_{name.replace(' ', '_').lower()}.png")
        
        if f1 > best_f1:
            best_f1 = f1
            best_model_name = name
            best_model = model
            
    print(f"\nBest model selected: {best_model_name} (F1-score: {best_f1:.4f})")
    
    # Save best model and vectorizer
    if not os.path.exists('models'):
        os.makedirs('models')
        
    joblib.dump(vectorizer, 'models/vectorizer.pkl')
    joblib.dump(best_model, 'models/classifier.pkl')
    print("Saved vectorizer and classifier to 'models/' directory.")

if __name__ == '__main__':
    main()
