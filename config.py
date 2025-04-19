import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
# In Cloud Run, service account credentials are automatically provided
IS_CLOUD_RUN = os.environ.get('K_SERVICE') is not None
if IS_CLOUD_RUN:
    logger.info("Running in Cloud Run environment")
    # Cloud Run automatically provides credentials, no need to set GOOGLE_APPLICATION_CREDENTIALS
    GOOGLE_APPLICATION_CREDENTIALS = None
else:
    logger.info("Running in local environment")
    # For local development, use service account file
    GOOGLE_APPLICATION_CREDENTIALS = os.environ.get(
        "GOOGLE_APPLICATION_CREDENTIALS", 
        os.path.join(BASE_DIR, "vc-interview-service-account.json")
    )
    if os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
        logger.info(f"Using service account from: {GOOGLE_APPLICATION_CREDENTIALS}")
    else:
        logger.warning(f"Service account file not found at: {GOOGLE_APPLICATION_CREDENTIALS}")

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "vc-interview-agent")
LOCATION = os.environ.get("GCP_LOCATION", "us-central1")

# No need for separate API key - using service account
API_KEY = None

# CSV path for questions
QUESTIONS_CSV_PATH = os.path.join(BASE_DIR, "data", "vc_interview_questions_full.csv")
if not os.path.exists(QUESTIONS_CSV_PATH):
    logger.error(f"Questions CSV file not found at: {QUESTIONS_CSV_PATH}")
else:
    logger.info(f"Questions CSV file found at: {QUESTIONS_CSV_PATH}")
