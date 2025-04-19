from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
import uvicorn
import os
import asyncio
from typing import Optional, List
import io

from config import API_TITLE, API_DESCRIPTION, API_VERSION, HOST, PORT
from models.schemas import (
    SessionCreate, SessionStatus, Question, Response,
    Feedback, InterviewResult, CVUpload, AudioUpload
)
from services.interview import InterviewService
from services.audio import generate_speech, transcribe_audio_file
from utils.helpers import validate_document_file, validate_audio_file, save_upload_file, clean_temp_files

# Create FastAPI app
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create interview service instance
interview_service = InterviewService()

# Periodic cleanup task
async def cleanup_task():
    """Periodically clean up old sessions and temporary files"""
    while True:
        try:
            # Clean up sessions older than 24 hours
            interview_service.cleanup_old_sessions(24)
            
            # Clean up temporary files older than 24 hours
            clean_temp_files(24)
        except Exception as e:
            print(f"Error in cleanup task: {e}")
        
        # Sleep for 1 hour before next cleanup
        await asyncio.sleep(3600)

@app.on_event("startup")
async def startup_event():
    """Start background tasks on application startup"""
    asyncio.create_task(cleanup_task())

# API endpoints
@app.post("/api/sessions", response_model=SessionCreate)
async def create_session():
    """Create a new interview session"""
    session_id = interview_service.create_session()
    return SessionCreate(session_id=session_id)

@app.get("/api/sessions/{session_id}", response_model=SessionStatus)
async def get_session_status(session_id: str):
    """Get the status of an interview session"""
    return interview_service.get_session_status(session_id)

@app.post("/api/sessions/{session_id}/cv", response_model=CVUpload)
async def upload_cv(session_id: str, file: UploadFile = File(...)):
    """Upload a CV and generate personalized questions"""
    # Validate file
    if not validate_document_file(file):
        raise HTTPException(status_code=400, detail="Invalid document format")
    
    # Process CV
    cv_path = await interview_service.process_cv(session_id, file)
    
    return CVUpload(
        file_path=cv_path,
        file_type=os.path.splitext(file.filename)[1].lower()
    )

@app.get("/api/sessions/{session_id}/questions/next", response_model=Optional[Question])
async def get_next_question(session_id: str):
    """Get the next question in the interview"""
    question = interview_service.get_next_question(session_id)
    if question is None:
        return JSONResponse(
            status_code=204,
            content={"detail": "No more questions available"}
        )
    return question

@app.post("/api/sessions/{session_id}/questions/{question_id}/response", response_model=Response)
async def submit_response(
    session_id: str, 
    question_id: str,
    text: Optional[str] = Form(None),
    audio_file: Optional[UploadFile] = File(None)
):
    """Submit a response to a question"""
    # Validate audio file if provided
    if audio_file and not validate_audio_file(audio_file):
        raise HTTPException(status_code=400, detail="Invalid audio format")
    
    # Process response
    return await interview_service.process_response(
        session_id, 
        question_id, 
        audio_file, 
        text
    )

@app.post("/api/sessions/{session_id}/feedback", response_model=Feedback)
async def generate_feedback(session_id: str):
    """Generate feedback for the completed interview"""
    return await interview_service.generate_feedback(session_id)

@app.get("/api/sessions/{session_id}/result", response_model=InterviewResult)
async def get_interview_result(session_id: str):
    """Get the complete interview result"""
    return interview_service.get_interview_result(session_id)

@app.post("/api/speech/generate")
async def text_to_speech(text: str, voice_type: Optional[str] = "male"):
    """Generate speech from text"""
    audio_content = await generate_speech(text, voice_type)
    
    # Return audio as a streaming response
    return StreamingResponse(
        io.BytesIO(audio_content),
        media_type="audio/wav"
    )

@app.post("/api/speech/transcribe", response_model=dict)
async def transcribe_audio(file: UploadFile = File(...), background_tasks: BackgroundTasks = BackgroundTasks()):
    """Transcribe audio file"""
    # Validate file
    if not validate_audio_file(file):
        raise HTTPException(status_code=400, detail="Invalid audio format")
    
    # Save file temporarily
    file_path = await save_upload_file(file)
    
    # Transcribe
    transcription = await transcribe_audio_file(file_path)
    
    # Clean up file in background
    def cleanup():
        try:
            os.remove(file_path)
        except:
            pass
    
    background_tasks.add_task(cleanup)
    
    return {"transcription": transcription}

if __name__ == "__main__":
    # Use the PORT environment variable provided by Cloud Run
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(
        "main:app", 
        host="0.0.0.0",  # Must listen on all interfaces for Cloud Run
        port=port,
        reload=False     # Disable reload in production
    )