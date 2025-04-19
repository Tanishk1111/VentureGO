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

# Copy the application code
COPY . .

# Create necessary directories
RUN mkdir -p sessions data

# Explicitly expose port 8080
EXPOSE 8080

# Set the entrypoint
CMD ["python", "main.py"]
