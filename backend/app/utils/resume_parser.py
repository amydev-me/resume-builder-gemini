# backend/app/utils/resume_parser.py

import io
from docx import Document # For DOCX files
import fitz # PyMuPDF for PDF files (import as fitz)
from typing import Optional

def extract_text_from_docx(docx_file: io.BytesIO) -> Optional[str]:
    """
    Extracts text from a DOCX file.
    Takes a BytesIO object representing the DOCX file.
    """
    try:
        document = Document(docx_file)
        full_text = []
        for para in document.paragraphs:
            full_text.append(para.text)
        return "\n".join(full_text)
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
        return None

def extract_text_from_pdf(pdf_file: io.BytesIO) -> Optional[str]:
    """
    Extracts text from a PDF file.
    Takes a BytesIO object representing the PDF file.
    """
    try:
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        text = ""
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

def parse_resume_content(file_content: bytes, filename: str) -> Optional[str]:
    """
    Parses the content of an uploaded resume file and returns its text.
    Supports .pdf and .docx.
    """
    file_extension = filename.split('.')[-1].lower()
    file_stream = io.BytesIO(file_content)

    if file_extension == 'pdf':
        return extract_text_from_pdf(file_stream)
    elif file_extension == 'docx':
        return extract_text_from_docx(file_stream)
    else:
        print(f"Unsupported file type: {file_extension}")
        return None