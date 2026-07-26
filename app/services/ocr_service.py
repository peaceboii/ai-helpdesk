import io
import PyPDF2
from typing import Optional

class OCRService:
    @staticmethod
    def extract_text(filename: str, file_bytes: bytes) -> str:
        """
        Extracts text from files. Supports PDF via PyPDF2.
        For images and other types, returns simulated OCR text.
        """
        if not file_bytes:
            return ""
            
        ext = filename.split('.')[-1].lower() if '.' in filename else ''
        
        if ext == 'pdf':
            try:
                pdf_file = io.BytesIO(file_bytes)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text = ""
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text.strip()
            except Exception as e:
                print(f"PDF Parsing error: {e}")
                return ""
        elif ext in ['png', 'jpg', 'jpeg', 'webp']:
            # Simulating OCR for image documents
            # For demonstration, check if it contains keywords in filename or generate typical mock OCR text
            filename_lower = filename.lower()
            if "invoice" in filename_lower:
                return "INVOICE #INV-2026-9908. Total Amount Due: $1,250.00. Payment due by 2026-08-15. Transaction ID: TXN-554422."
            elif "server" in filename_lower or "error" in filename_lower:
                return "FATAL ERROR: Server down. Production database connection failed. ASAP support needed."
            elif "salary" in filename_lower or "pay" in filename_lower:
                return "Employee ID: EMP-45302. Salary discrepancy for July 2026. Gross amount missing."
            else:
                return f"[OCR Extracted Text from {filename}]: This is a simulated text extract from the attachment."
        return ""
