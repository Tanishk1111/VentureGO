import os
from typing import Optional
import PyPDF2
import docx

def extract_text_from_cv(cv_path: str) -> Optional[str]:
    """Extract text content from a CV file (PDF or DOCX)"""
    text = ""
    file_extension = os.path.splitext(cv_path)[1].lower()
    
    try:
        if file_extension == '.pdf':
            # Process PDF file
            with open(cv_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
                    
        elif file_extension in ['.docx', '.doc']:
            # Process Word document
            doc = docx.Document(cv_path)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
                
        else:
            # For text files or other formats
            with open(cv_path, 'r', encoding='utf-8', errors='ignore') as file:
                text = file.read()
                
        return text
    except Exception as e:
        print(f"Error extracting text from CV: {e}")
        return None
