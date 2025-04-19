from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class CVUpload(BaseModel):
    file_path: str
    file_type: str

class AudioUpload(BaseModel):
    file_path: str
    duration: Optional[float] = None

class SessionCreate(BaseModel):
    session_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))

class SessionStatus(BaseModel):
    session_id: str
    status: str
    current_question_index: int
    total_questions: int
    created_at: datetime = Field(default_factory=datetime.now)
    cv_path: Optional[str] = None

class Question(BaseModel):
    question_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    type: str = "standard"  # "standard" or "cv_based"
    expected_response: Optional[str] = None

class Response(BaseModel):
    response_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question_id: str
    text: str
    audio_path: Optional[str] = None
    sentiment_score: Optional[float] = None
    
class Feedback(BaseModel):
    summary: str
    detailed_feedback: Dict[str, str]
    overall_score: Optional[float] = None

class InterviewResult(BaseModel):
    session_id: str
    questions: List[Question]
    responses: List[Response]
    feedback: Optional[Feedback] = None
    duration: float
