import fitz  # PyMuPDF
import pdfplumber
from typing import Optional, Dict
import os

class FileParser:
    @staticmethod
    def parse_pdf_pymupdf(file_path: str) -> Dict[str, any]:
        try:
            doc = fitz.open(file_path)
            text = ""
            pages_count = len(doc)
            
            for page_num in range(pages_count):
                page = doc[page_num]
                text += page.get_text()
            
            doc.close()
            
            return {
                'content': text.strip(),
                'pages_count': pages_count,
                'success': True,
                'error': None
            }
        except Exception as e:
            return {
                'content': '',
                'pages_count': 0,
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def parse_pdf_pdfplumber(file_path: str) -> Dict[str, any]:
        try:
            text = ""
            pages_count = 0
            
            with pdfplumber.open(file_path) as pdf:
                pages_count = len(pdf.pages)
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            return {
                'content': text.strip(),
                'pages_count': pages_count,
                'success': True,
                'error': None
            }
        except Exception as e:
            return {
                'content': '',
                'pages_count': 0,
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def parse_pdf(file_path: str, method: str = 'pymupdf') -> Dict[str, any]:
        if not os.path.exists(file_path):
            return {
                'content': '',
                'pages_count': 0,
                'success': False,
                'error': 'File not found'
            }
        
        if method == 'pdfplumber':
            result = FileParser.parse_pdf_pdfplumber(file_path)
        else:
            result = FileParser.parse_pdf_pymupdf(file_path)

        if not result['success'] and method == 'pymupdf':
            print(f"PyMuPDF failed, trying pdfplumber...")
            result = FileParser.parse_pdf_pdfplumber(file_path)
        elif not result['success'] and method == 'pdfplumber':
            print(f"pdfplumber failed, trying PyMuPDF...")
            result = FileParser.parse_pdf_pymupdf(file_path)
        
        return result
    
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
        if not text:
            return []
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]

            if end < text_length:
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > chunk_size * 0.5:
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk.strip())
            start = end - overlap
        
        return chunks
