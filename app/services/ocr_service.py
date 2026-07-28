import io
import os
import zipfile
import xml.etree.ElementTree as ET
import PyPDF2
from typing import Optional

class OCRService:
    @staticmethod
    def extract_text(filename: str, file_bytes: bytes) -> str:
        """
        Extracts text from files. Supports PDF (PyPDF2), DOCX (built-in XML zip parser),
        TXT (UTF-8 decode), and ZIP archives (recursive extraction of nested files).
        For images, returns simulated OCR text.
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
                
        elif ext == 'txt':
            try:
                return file_bytes.decode('utf-8', errors='ignore').strip()
            except Exception as e:
                print(f"TXT Parsing error: {e}")
                return ""
                
        elif ext == 'docx':
            try:
                with zipfile.ZipFile(io.BytesIO(file_bytes)) as docx:
                    xml_content = docx.read('word/document.xml')
                    root = ET.fromstring(xml_content)
                    namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                    paragraphs = []
                    for p in root.findall('.//w:p', namespaces):
                        texts = [t.text for t in p.findall('.//w:t', namespaces) if t.text]
                        if texts:
                            paragraphs.append("".join(texts))
                    return "\n".join(paragraphs).strip()
            except Exception as e:
                print(f"DOCX Parsing error: {e}")
                return ""
                
        elif ext == 'zip':
            try:
                extracted_texts = []
                with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                    for name in z.namelist():
                        if name.endswith('/'):
                            continue
                        nested_bytes = z.read(name)
                        nested_text = OCRService.extract_text(name, nested_bytes)
                        if nested_text:
                            extracted_texts.append(f"--- File: {os.path.basename(name)} inside ZIP ---\n{nested_text}")
                # Note: os might need import, or just use name.split('/')[-1]
                return "\n\n".join(extracted_texts).strip()
            except Exception as e:
                print(f"ZIP Parsing error: {e}")
                return ""
                
        elif ext in ['png', 'jpg', 'jpeg', 'webp']:
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
