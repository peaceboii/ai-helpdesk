import re
from typing import Dict, Any

class EntityExtractionService:
    @staticmethod
    def extract_entities(text: str) -> Dict[str, Any]:
        """
        Extracts structured entities from ticket text:
        - Invoice Number (e.g. INV-2026-9908)
        - Order Number (e.g. ORD-12345)
        - Transaction ID (e.g. TXN-554422)
        - Employee ID (e.g. EMP-9823)
        - Phone Number
        - Amount ($ USD)
        - Date (YYYY-MM-DD or MM/DD/YYYY)
        """
        entities = {}
        
        # 1. Invoice Number
        invoice_match = re.search(r'(?i)inv(?:oice)?\s*#?\s*([a-z0-9-]+)', text)
        if invoice_match:
            entities['Invoice Number'] = invoice_match.group(1).upper()
            
        # 2. Order Number
        order_match = re.search(r'(?i)ord(?:er)?\s*#?\s*([a-z0-9-]+)', text)
        if order_match:
            entities['Order Number'] = order_match.group(1).upper()
            
        # 3. Transaction ID
        txn_match = re.search(r'(?i)txn|transaction(?:\s*id)?\s*#?\s*([a-z0-9-]+)', text)
        if txn_match:
            entities['Transaction ID'] = txn_match.group(1).upper()
            
        # 4. Employee ID
        emp_match = re.search(r'(?i)emp(?:loyee)?(?:\s*id)?\s*#?\s*([a-z0-9-]+)', text)
        if emp_match:
            entities['Employee ID'] = emp_match.group(1).upper()
            
        # 5. Phone Number
        phone_match = re.search(r'\+?\d{1,4}[-.\s]?\(?\d{1,3}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}', text)
        if phone_match and len(phone_match.group(0).strip()) > 7:
            entities['Phone'] = phone_match.group(0).strip()
            
        # 6. Amount
        amount_match = re.search(r'\$\d+(?:,\d{3})*(?:\.\d{2})?', text)
        if amount_match:
            entities['Amount'] = amount_match.group(0)
            
        # 7. Date
        date_match = re.search(r'\b\d{4}[-/]\d{2}[-/]\d{2}\b|\b\d{2}[-/]\d{2}[-/]\d{4}\b', text)
        if date_match:
            entities['Date'] = date_match.group(0)
            
        return entities
