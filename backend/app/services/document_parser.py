import PyPDF2
from docx import Document as DocxDocument
from typing import List, Dict
import io

class DocumentParser:
    @staticmethod
    def parse_pdf(file_content: bytes) -> List[Dict]:
        """Extract text from PDF with page numbers"""
        pages = []
        try:
            pdf_file = io.BytesIO(file_content)
            reader = PyPDF2.PdfReader(pdf_file)
            for page_num, page in enumerate(reader.pages, 1):
                text = page.extract_text()
                if text and text.strip():
                    pages.append({
                        "content": text,
                        "page": page_num,
                        "metadata": {"page": page_num}
                    })
        except Exception as e:
            raise ValueError(f"Failed to parse PDF: {str(e)}")
        return pages
    
    @staticmethod
    def parse_docx(file_content: bytes) -> List[Dict]:
        """Extract text from DOCX"""
        try:
            docx_file = io.BytesIO(file_content)
            doc = DocxDocument(docx_file)
            content = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
            return [{
                "content": content,
                "page": 1,
                "metadata": {"page": 1}
            }]
        except Exception as e:
            raise ValueError(f"Failed to parse DOCX: {str(e)}")
    
    @staticmethod
    def parse_txt(file_content: bytes) -> List[Dict]:
        """Extract text from TXT file"""
        try:
            content = file_content.decode('utf-8')
            return [{
                "content": content,
                "page": 1,
                "metadata": {"page": 1}
            }]
        except Exception as e:
            raise ValueError(f"Failed to parse TXT: {str(e)}")