import re
import string
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

# Ensure necessary NLTK datasets are downloaded
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet', quiet=True)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab', quiet=True)


def clean_text(text: str) -> str:
    """
    Cleans the input text according to NLP best practices:
    - Lowercase
    - Remove HTML
    - Remove URLs
    - Remove punctuation
    - Remove numbers
    - Remove stopwords
    - Tokenize
    - Lemmatize
    """
    if not isinstance(text, str):
        return ""
        
    # 1. Lowercase
    text = text.lower()
    
    # 2. Remove HTML
    text = re.sub(r'<[^>]+>', '', text)
    
    # 3. Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    
    # 4. Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    
    # 5. Remove numbers
    text = re.sub(r'\d+', '', text)
    
    # 6. Tokenize
    tokens = word_tokenize(text)
    
    # 7. Remove stopwords & 8. Lemmatize
    stop_words = set(stopwords.words('english'))
    lemmatizer = WordNetLemmatizer()
    
    clean_tokens = [
        lemmatizer.lemmatize(word) 
        for word in tokens 
        if word not in stop_words
    ]
    
    return " ".join(clean_tokens)

def detect_priority(text: str) -> str:
    """
    Detects if the priority of a ticket is HIGH based on keywords.
    Otherwise returns NORMAL.
    """
    text_lower = str(text).lower()
    keywords = [
        'urgent', 'critical', 'down', 'server down', 
        'production', 'payment failed', 'salary', 
        'invoice', 'not working', 'asap'
    ]
    
    for kw in keywords:
        if kw in text_lower:
            return "HIGH"
    return "NORMAL"
