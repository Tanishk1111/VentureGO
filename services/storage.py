import os
import json
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
from config import SESSIONS_DIR

class StorageService:
    """Service for storing and retrieving session data"""
    
    @staticmethod
    def save_session(session_id: str, data: Dict[str, Any]) -> bool:
        """Save session data to disk"""
        try:
            # Create session directory if it doesn't exist
            session_dir = Path(SESSIONS_DIR) / session_id
            os.makedirs(session_dir, exist_ok=True)
            
            # Remove any non-serializable data
            serializable_data = {k: v for k, v in data.items() if k not in ["session_dir"]}
            
            # Save the data
            with open(session_dir / "session.json", "w") as f:
                json.dump(serializable_data, f, indent=2, default=str)
                
            return True
        except Exception as e:
            print(f"Error saving session {session_id}: {e}")
            return False
    
    @staticmethod
    def load_session(session_id: str) -> Optional[Dict[str, Any]]:
        """Load session data from disk"""
        try:
            session_dir = Path(SESSIONS_DIR) / session_id
            session_file = session_dir / "session.json"
            
            if not session_file.exists():
                return None
                
            with open(session_file, "r") as f:
                data = json.load(f)
                
            # Add session directory for convenience
            data["session_dir"] = str(session_dir)
                
            return data
        except Exception as e:
            print(f"Error loading session {session_id}: {e}")
            return None
    
    @staticmethod
    def list_sessions(max_age_hours: Optional[int] = None) -> List[str]:
        """List all session IDs, optionally filtering by age"""
        sessions = []
        
        try:
            sessions_path = Path(SESSIONS_DIR)
            for item in sessions_path.iterdir():
                if item.is_dir():
                    session_id = item.name
                    
                    # Check session age if requested
                    if max_age_hours is not None:
                        session_file = item / "session.json"
                        if session_file.exists():
                            file_age = time.time() - session_file.stat().st_mtime
                            max_age_seconds = max_age_hours * 3600
                            if file_age > max_age_seconds:
                                continue
                    
                    sessions.append(session_id)
                    
            return sessions
        except Exception as e:
            print(f"Error listing sessions: {e}")
            return []
    
    @staticmethod
    def delete_session(session_id: str) -> bool:
        """Delete a session and all its data"""
        try:
            import shutil
            session_dir = Path(SESSIONS_DIR) / session_id
            if session_dir.exists():
                shutil.rmtree(session_dir)
            return True
        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
            return False
