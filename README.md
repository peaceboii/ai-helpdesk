# 🎫 AI Helpdesk Automation Platform

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge.svg)](https://ai-appdesk-ieu9rww5efkwdk3zdxwbna.streamlit.app/)

A production-quality Helpdesk Automation Platform that manages ticket creation, cleans data via NLP pipelines, detects urgency, maps categories, and orchestrates auto-responses.

**Live Application Link:** [https://ai-appdesk-ieu9rww5efkwdk3zdxwbna.streamlit.app/](https://ai-appdesk-ieu9rww5efkwdk3zdxwbna.streamlit.app/)

---

## 📌 Problem Statement
Customer support teams handle a massive volume of tickets daily. Manually routing these tickets to the appropriate department (Billing, Technical, HR, General) is time-consuming and error-prone. This project automates the entire ingestion and classification lifecycle, routing issues to specialized teams and raising responses within minutes.

## 🗺️ Architectural Workflow
```
             [Customer Submissions] (Email, WhatsApp, Slack, Telegram, REST API, Web Form)
                                      |
                                      v
                        [Factory Ingestion Connectors]
                                      |
                                      v
                     [Orchestration Engine Pipeline]
                                      |
     +--------------------------------+-------------------------------+
     |                |               |               |               |
[Validation]     [OCR Parser]   [Spam Filter]  [Lang Translate]  [Duplicate Checks]
     |                |               |               |               |
     +--------------------------------+-------------------------------+
                                      |
                                      v
                      [Regex Entity Extraction Service]
                                      |
                                      v
                     [Sentiment & Urgency Classifier]
                                      |
                                      v
                   [AI Categorizer (Logistic Regression)]
                                      |
                                      v
                        [Routing & Assignment Engine]
                                      |
                                      v
                    [SQLite Repository & Auto-Response]
```

---

## 🚀 Key Modules & Features

### 1. Ingestion & Connectors (Factory Pattern)
Normalizes payloads from diverse channels (Email via IMAP, WhatsApp, Slack, Telegram webhooks, REST API, and Manual Entry forms) into a uniform internal `Ticket` object.

### 2. Validation & Spam Filtering
Checks required fields and email formats. Reject tickets that exceed size limits. Block marketing emails or blank requests based on configuration rules.

### 3. Cosine Similarity Duplicate Checker
Computes TF-IDF Cosine Similarity of incoming text against existing tickets. If >90% similarity is found, flags the ticket and provides a merge-and-resolve workflow.

### 4. Language Translation & OCR
Uses `langdetect` to identify non-English tickets, translating them to English. Extracts text from PDF documents (using PyPDF2) and image attachments (OCR), appending it to the ticket body for classification.

### 5. Entity Extraction
Regex-based parses for Order numbers, Invoices, Transaction IDs, Employee IDs, Phone numbers, Amounts, and Dates, registering them as metadata.

### 6. Sentiment Analysis & Priority Escalar
Rates user sentiment (Positive, Neutral, Negative, Very Angry). Tickets tagged as "Very Angry" are automatically escalated to `HIGH` priority.

### 7. Scikit-Learn Classification
Vectorizes cleaned text with TF-IDF (`max_features=5000`, `ngram_range=(1,2)`) and routes through a trained **Logistic Regression** classifier (accuracy ~42%). Falls back to **"Needs Human Review"** if confidence falls below 60%.

---

## 🛠️ How to Run Locally

### 1. Setup Virtual Environment & Dependencies
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Ingest Data & Train Classifier
```bash
# Ingest Kaggle dataset
python data/download_data.py
python data/preprocess.py

# Train models
python train.py
```

### 3. Launch the Platform
Start the FastAPI server (exposing webhooks and REST endpoints):
```bash
uvicorn app.api.main:app --port 8000
```

Start the Streamlit dashboard in a separate terminal:
```bash
streamlit run app.py
```

---

## 🎯 Model Evaluation Results
We compared two baseline models for text classification:

| Model | Accuracy | Weighted Precision | Weighted Recall | Weighted F1-score |
|---|---|---|---|---|
| Multinomial Naive Bayes | 42.08% | 34.53% | 42.08% | 37.87% |
| **Logistic Regression** | **42.25%** | **37.58%** | **42.25%** | **38.42%** |

*Logistic Regression was automatically selected as the active model due to a higher F1-score.*

---

## 🔮 Future Roadmap
- Replace rule-based sentiment/translation with LLMs (e.g. Gemini API).
- Add active IMAP listening in a background daemon thread.
- Implement automated email dispatching instead of console/DB simulated responses.
