# AI-Powered Support Ticket Categorization System

## Problem Statement
Customer support teams handle a massive volume of tickets daily. Manually routing these tickets to the appropriate department (Billing, Technical, HR, General) is time-consuming and error-prone. This project aims to automate this process using an AI-powered text classification model, improving efficiency and response times.

## Dataset
The project uses a customer support ticket dataset containing ticket subjects and descriptions. We mapped the given categories to the four target classes (Billing, Technical, HR, General). A synthetic dataset for HR was created to ensure balanced representation for the prompt's requirements.

## Approach
We built a text classification pipeline using Python and Scikit-Learn. The system preprocesses the text, extracts TF-IDF features, and trains both Multinomial Naive Bayes and Logistic Regression models. The best model is selected and deployed via a Streamlit web application.

## Pipeline Diagram
```
[Raw Data] -> [Preprocessing (Clean, Tokenize, Lemmatize)] -> [TF-IDF Vectorizer]
                                                                     |
                                                          [Train NB & Logistic Reg]
                                                                     |
                                                          [Select Best Model]
                                                                     |
[User Input via Streamlit] -> [Saved Vectorizer & Model] -> [Prediction & Priority]
```

## Preprocessing
Text data is extremely noisy. Our preprocessing pipeline (in `utils.py`) handles:
- Lowercasing to ensure case-insensitivity.
- Removing HTML tags and URLs.
- Removing punctuation and numbers.
- Tokenization to split text into words.
- Removing English stopwords (e.g., "the", "is", "at").
- Lemmatization to reduce words to their base form (e.g., "running" -> "run").

## TF-IDF Explanation
Term Frequency-Inverse Document Frequency (TF-IDF) is used to convert text into numerical vectors. 
- **TF (Term Frequency)**: Measures how frequently a term appears in a document.
- **IDF (Inverse Document Frequency)**: Measures how important a term is across the entire dataset. It heavily penalizes common words and boosts rare, domain-specific words.
We used `max_features=5000` to limit the vocabulary size and `ngram_range=(1,2)` to capture single words and two-word phrases (bigrams).

## Model Comparison
We compared two baseline models for text classification:
1. **Multinomial Naive Bayes**: A generative model that works well with word counts and TF-IDF. It assumes independence between features.
2. **Logistic Regression**: A discriminative model that often performs better when features are somewhat correlated.

## Results
The Logistic Regression model generally outperforms Naive Bayes in both F1-score and Accuracy for this dataset, thanks to its ability to handle complex feature weights.

## How to Run

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Generate Data**:
   ```bash
   cd data
   python download_data.py
   python preprocess.py
   cd ..
   ```

3. **Train the Model**:
   ```bash
   python train.py
   ```

4. **Run CLI Prediction**:
   ```bash
   python predict.py
   ```

5. **Run Streamlit Web App**:
   ```bash
   streamlit run app.py
   ```

## Screenshots
*(Add screenshots of the Streamlit app here)*

## Future Improvements
- Implement transformer-based models like BERT for better contextual understanding.
- Add hyperparameter tuning via GridSearchCV.
- Gather more real-world HR data to replace synthetic data.
