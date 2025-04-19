import os
import time
import asyncio
import pandas as pd
from typing import List, Dict, Optional, Any, Tuple
import uuid
import json
from pathlib import Path

import google.generativeai as genai
from fastapi import UploadFile, HTTPException

from config import QUESTIONS_CSV_PATH, API_KEY, SESSIONS_DIR
from models.schemas import Question, Response, SessionStatus, Feedback, InterviewResult
from services.document import extract_text_from_cv
from services.audio import transcribe_audio_file
from services.analysis import analyze_responses, analyze_sentiment

# Configure Gemini
genai.configure(api_key=API_KEY)

class InterviewService:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.load_questions()
    
    def load_questions(self) -> None:
        """Load standard interview questions from CSV"""
        try:
            df = pd.read_csv(QUESTIONS_CSV_PATH)
            self.standard_questions = []
            for _, row in df.iterrows():
                self.standard_questions.append({
                    "text": row['Question'],
                    "expected_response": row['Expected Response']
                })
        except Exception as e:
            print(f"Error loading questions: {e}")
            # Fallback questions
            self.standard_questions = [
                {
                    "text": "Tell me about your startup.",
                    "expected_response": "Clear explanation of the startup concept and vision."
                },
                {
                    "text": "What problem are you solving?",
                    "expected_response": "Specific problem statement with market impact."
                },
                {
                    "text": "Who are your target customers?",
                    "expected_response": "Detailed customer segmentation with clear needs."
                }
            ]
    
    def create_session(self) -> str:
        """Create a new interview session"""
        session_id = str(uuid.uuid4())
        session_dir = os.path.join(SESSIONS_DIR, session_id)
        os.makedirs(session_dir, exist_ok=True)
        
        self.sessions[session_id] = {
            "created_at": time.time(),
            "status": "created",
            "questions": [],
            "responses": [],
            "current_index": 0,
            "cv_path": None,
            "session_dir": session_dir
        }
        
        # Save session metadata
        self._save_session_metadata(session_id)
        
        return session_id
    
    def _save_session_metadata(self, session_id: str) -> None:
        """Save session metadata to file"""
        if session_id not in self.sessions:
            return
            
        session = self.sessions[session_id]
        session_dir = session["session_dir"]
        
        # Create a serializable copy of the session data
        metadata = {
            "session_id": session_id,
            "created_at": session["created_at"],
            "status": session["status"],
            "current_index": session["current_index"],
            "cv_path": session["cv_path"],
            "questions": [
                {"text": q["text"], "type": q["type"]} 
                for q in session["questions"]
            ],
            "responses": [
                {"question_index": i, "text": r["text"]} 
                for i, r in enumerate(session["responses"])
            ]
        }
        
        # Save metadata
        with open(os.path.join(session_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)
    
    def get_session_status(self, session_id: str) -> SessionStatus:
        """Get current status of an interview session"""
        if session_id not in self.sessions:
            raise HTTPException(status_code=404, detail="Session not found")
            
        session = self.sessions[session_id]
        
        return SessionStatus(
            session_id=session_id,
            status=session["status"],
            current_question_index=session["current_index"],
            total_questions=len(session["questions"]),
            created_at=session["created_at"],
            cv_path=session["cv_path"]
        )
    
    async def process_cv(self, session_id: str, file: UploadFile) -> str:
        """Process CV and generate personalized questions"""
        if session_id not in self.sessions:
            raise HTTPException(status_code=404, detail="Session not found")
            
        session = self.sessions[session_id]
        
        # Save the uploaded CV
        cv_path = os.path.join(session["session_dir"], f"cv_{file.filename}")
        with open(cv_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Extract text from CV
        cv_text = extract_text_from_cv(cv_path)
        
        if not cv_text:
            raise HTTPException(status_code=422, detail="Could not extract text from CV")
        
        # Generate CV-based questions
        cv_questions = await self._generate_cv_questions(cv_text)
        
        # Update session with CV path and questions
        session["cv_path"] = cv_path
        session["questions"] = [
            {"text": q, "type": "cv_based", "expected_response": "Detailed response connecting experience to startup"} 
            for q in cv_questions
        ] + [
            {"text": q["text"], "type": "standard", "expected_response": q["expected_response"]} 
            for q in self.standard_questions
        ]
        
        session["status"] = "ready"
        self._save_session_metadata(session_id)
        
        return cv_path
    
    async def _generate_cv_questions(self, cv_text: str) -> List[str]:
        """Generate interview questions based on CV content"""
        try:
            prompt = f"""
            Based on this candidate's CV, generate 2 specific, personalized interview questions
            that would be appropriate for a VC interview. Focus on their experience, skills,
            or background that would be relevant to a startup founder seeking investment.
            
            CV Content:
            {cv_text[:1500]}  # Limit content to avoid token limits
            
            Return exactly 2 questions, each on a new line without numbering or additional text.
            """
            
            model = genai.GenerativeModel('gemini-1.5-pro-latest')
            response = model.generate_content(prompt)
            
            if hasattr(response, 'text'):
                # Split by newline to get individual questions
                questions = [q.strip() for q in response.text.strip().split('\n') if q.strip()]
                # Return up to 2 questions
                return questions[:2]
        except Exception as e:
            print(f"Error generating CV questions: {e}")
        
        # Fallback questions
        return [
            "Based on your CV, what relevant experience would help you succeed in this venture?",
            "How do your past achievements prepare you for the challenges of this startup?"
        ]
    
    def get_next_question(self, session_id: str) -> Optional[Question]:
        """Get the next question in the interview"""
        if session_id not in self.sessions:
            raise HTTPException(status_code=404, detail="Session not found")
            
        session = self.sessions[session_id]
        
        if session["status"] not in ["ready", "in_progress"]:
            raise HTTPException(status_code=400, detail=f"Session is in {session['status']} state")
            
        if session["current_index"] >= len(session["questions"]):
            return None
            
        current_q = session["questions"][session["current_index"]]
        
        # Update session status
        if session["status"] == "ready":
            session["status"] = "in_progress"
            self._save_session_metadata(session_id)
        
        return Question(
            question_id=f"{session_id}_{session['current_index']}",
            text=current_q["text"],
            type=current_q["type"],
            expected_response=current_q["expected_response"]
        )
    
    async def process_response(self, session_id: str, question_id: str, 
                          audio_file: Optional[UploadFile] = None, 
                          text: Optional[str] = None) -> Response:
        """Process a candidate's response to a question"""
        if session_id not in self.sessions:
            raise HTTPException(status_code=404, detail="Session not found")
            
        session = self.sessions[session_id]
        
        if session["status"] != "in_progress":
            raise HTTPException(status_code=400, detail=f"Session is in {session['status']} state")
        
        # Verify the question ID matches the current question
        expected_id = f"{session_id}_{session['current_index']}"
        if question_id != expected_id:
            raise HTTPException(status_code=400, detail="Question ID doesn't match current question")
        
        # Process audio file if provided
        audio_path = None
        if audio_file:
            try:
                audio_path = os.path.join(
                    session["session_dir"], 
                    f"response_{session['current_index']}.wav"
                )
                
                # Save audio file
                with open(audio_path, "wb") as buffer:
                    content = await audio_file.read()
                    buffer.write(content)
                
                # If no text is provided, transcribe the audio
                if not text:
                    text = await transcribe_audio_file(audio_path)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")
        
        if not text:
            raise HTTPException(status_code=400, detail="No response text or audio provided")
        
        # Analyze sentiment
        sentiment = analyze_sentiment(text)
        
        # Create response object
        response = {
            "text": text,
            "audio_path": audio_path,
            "sentiment": sentiment,
            "timestamp": time.time()
        }
        
        # Save response to session
        session["responses"].append(response)
        
        # Move to next question
        session["current_index"] += 1
        
        # Check if interview is complete
        if session["current_index"] >= len(session["questions"]):
            session["status"] = "completed"
        
        # Save updated session data
        self._save_session_metadata(session_id)
        
        return Response(
            response_id=f"{session_id}_response_{len(session['responses'])-1}",
            question_id=question_id,
            text=text,
            audio_path=audio_path,
            sentiment_score=sentiment["score"] if sentiment else None
        )
    
    async def generate_feedback(self, session_id: str) -> Feedback:
        """Generate feedback for the completed interview"""
        if session_id not in self.sessions:
            raise HTTPException(status_code=404, detail="Session not found")
            
        session = self.sessions[session_id]
        
        # Check if we have all responses
        if len(session["responses"]) < len(session["questions"]):
            raise HTTPException(
                status_code=400, 
                detail=f"Interview incomplete: {len(session['responses'])}/{len(session['questions'])} questions answered"
            )
        
        # Prepare data for analysis
        questions = [q["text"] for q in session["questions"]]
        expected_responses = [q["expected_response"] for q in session["questions"]]
        actual_responses = [r["text"] for r in session["responses"]]
        
        # Generate feedback
        feedback_result = await analyze_responses(
            actual_responses, 
            expected_responses, 
            questions
        )
        
        # Save feedback to session
        session["feedback"] = feedback_result
        session["status"] = "analyzed"
        self._save_session_metadata(session_id)
        
        # Create detailed feedback dict
        detailed_feedback = {}
        for i, question in enumerate(questions):
            if i < len(actual_responses):
                q_id = f"question_{i+1}"
                detailed_feedback[q_id] = feedback_result["detailed_feedback"].get(
                    q_id, "No detailed feedback available"
                )
        
        return Feedback(
            summary=feedback_result["summary"],
            detailed_feedback=detailed_feedback,
            overall_score=feedback_result.get("score", None)
        )
    
    def get_interview_result(self, session_id: str) -> InterviewResult:
        """Get the complete interview result including questions, responses and feedback"""
        if session_id not in self.sessions:
            raise HTTPException(status_code=404, detail="Session not found")
            
        session = self.sessions[session_id]
        
        # Create Question objects
        questions = []
        for i, q in enumerate(session["questions"]):
            questions.append(Question(
                question_id=f"{session_id}_{i}",
                text=q["text"],
                type=q["type"],
                expected_response=q["expected_response"]
            ))
        
        # Create Response objects
        responses = []
        for i, r in enumerate(session["responses"]):
            responses.append(Response(
                response_id=f"{session_id}_response_{i}",
                question_id=f"{session_id}_{i}",
                text=r["text"],
                audio_path=r.get("audio_path"),
                sentiment_score=r.get("sentiment", {}).get("score")
            ))
        
        # Create Feedback object if available
        feedback = None
        if "feedback" in session and session["feedback"]:
            detailed_feedback = {}
            if "detailed_feedback" in session["feedback"]:
                for i, q in enumerate(session["questions"]):
                    if i < len(session["responses"]):
                        q_id = f"question_{i+1}"
                        detailed_feedback[q_id] = session["feedback"]["detailed_feedback"].get(
                            q_id, "No detailed feedback available"
                        )
            
            feedback = Feedback(
                summary=session["feedback"].get("summary", "No summary available"),
                detailed_feedback=detailed_feedback,
                overall_score=session["feedback"].get("score")
            )
        
        # Calculate duration
        created_at = session.get("created_at", 0)
        last_response_time = session["responses"][-1]["timestamp"] if session["responses"] else time.time()
        duration = last_response_time - created_at
        
        return InterviewResult(
            session_id=session_id,
            questions=questions,
            responses=responses,
            feedback=feedback,
            duration=duration
        )
    
    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up sessions older than the specified age"""
        now = time.time()
        max_age_seconds = max_age_hours * 3600
        
        sessions_to_remove = []
        for session_id, session in self.sessions.items():
            if now - session["created_at"] > max_age_seconds:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.sessions[session_id]
        
        return len(sessions_to_remove)
