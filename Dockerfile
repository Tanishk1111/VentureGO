FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    python3-pyaudio \
    && rm -rf /var/lib/apt/lists/*

# Pin NumPy to version below 2.0 to avoid compatibility issues
RUN pip install "numpy<2.0.0" --force-reinstall

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p sessions data temp uploads

# Copy the application code
COPY . .

# Ensure the CSV file is in the data directory
RUN if [ -f vc_interview_questions_full.csv ] && [ ! -f data/vc_interview_questions_full.csv ]; then \
    cp vc_interview_questions_full.csv data/vc_interview_questions_full.csv; \
    fi

# Make sure directories have correct permissions
RUN chmod -R 755 /app/data /app/sessions /app/temp /app/uploads

# Verify CSV file exists
RUN ls -la /app/data/vc_interview_questions_full.csv || echo "WARNING: CSV file not found"

# Explicitly expose port 8080
EXPOSE 8080

# Environment variables for better logging
ENV PYTHONUNBUFFERED=1

# Set the entrypoint
CMD ["python", "main.py"]
