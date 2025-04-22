FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    python3-pyaudio \
    && rm -rf /var/lib/apt/lists/*

# Fix NumPy compatibility issue with pandas
RUN pip install "numpy<2.0.0" --force-reinstall

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create necessary directories
RUN mkdir -p sessions data

# Expose port 8080
EXPOSE 8080

# Run the application
CMD ["python", "main.py"]
