import os
import time
import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import UploadFile, HTTPException

from config import UPLOADS_DIR, TEMP_DIR

def validate_file_extension(file: UploadFile, allowed_extensions: List[str]) -> bool:
    """Validate that a file has an allowed extension"""
    ext = os.path.splitext(file.filename)[1].lower()
    return ext in allowed_extensions

def validate_audio_file(file: UploadFile) -> bool:
    """Validate that a file is an audio file"""
    return validate_file_extension(file, ['.wav', '.mp3', '.ogg', '.m4a'])

def validate_document_file(file: UploadFile) -> bool:
    """Validate that a file is a document file"""
    return validate_file_extension(file, ['.pdf', '.docx', '.doc', '.txt'])

async def save_upload_file(file: UploadFile, directory: str = None) -> str:
    """Save an uploaded file and return the file path"""
    if directory is None:
        directory = UPLOADS_DIR
        
    # Create directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)
    
    # Generate a unique filename
    timestamp = int(time.time())
    unique_id = str(uuid.uuid4().hex)
    filename = f"{timestamp}_{unique_id}_{file.filename}"
    file_path = os.path.join(directory, filename)
    
    # Save the file
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
            
        return file_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")

def create_temp_file(prefix: str = "temp", suffix: str = "") -> str:
    """Create a temporary file and return its path"""
    # Create temp directory if it doesn't exist
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    # Generate a unique filename
    timestamp = int(time.time())
    unique_id = str(uuid.uuid4().hex)
    filename = f"{prefix}_{timestamp}_{unique_id}{suffix}"
    file_path = os.path.join(TEMP_DIR, filename)
    
    # Create an empty file
    with open(file_path, "wb") as f:
        pass
        
    return file_path

def clean_temp_files(max_age_hours: int = 24) -> int:
    """Clean up temporary files older than the specified age"""
    max_age_seconds = max_age_hours * 3600
    now = time.time()
    count = 0
    
    for item in Path(TEMP_DIR).glob("*"):
        if item.is_file():
            file_age = now - item.stat().st_mtime
            if file_age > max_age_seconds:
                try:
                    os.remove(item)
                    count += 1
                except Exception as e:
                    print(f"Error removing temp file {item}: {e}")
    
    return count
