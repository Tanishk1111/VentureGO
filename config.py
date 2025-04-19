import os
from pathlib import Path

# API settings
API_TITLE = "VC Interview API"
API_DESCRIPTION = "API for conducting venture capitalist interviews"
API_VERSION = "1.0.0"
HOST = "0.0.0.0"
PORT = 8080

# Session settings
SESSION_LIFETIME = 3600  # 1 hour

# Audio settings
AUDIO_FORMAT = "LINEAR16"
RATE = 16000
CHANNELS = 1

# Paths
BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp"
UPLOADS_DIR = BASE_DIR / "uploads"
SESSIONS_DIR = BASE_DIR / "sessions"

# Create necessary directories
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(SESSIONS_DIR, exist_ok=True)

# Google Cloud settings
GOOGLE_APPLICATION_CREDENTIALS = os.environ.get(
    "GOOGLE_APPLICATION_CREDENTIALS", 
    os.path.join(BASE_DIR, "vc-interview-agent-credentials.json")
)
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "vc-interview-agent")
LOCATION = os.environ.get("GCP_LOCATION", "us-central1")
API_KEY = os.environ.get("GEMINI_API_KEY", "your-api-key-here")

# CSV path for questions
QUESTIONS_CSV_PATH = os.path.join(BASE_DIR, "data", "vc_interview_questions_full.csv")
