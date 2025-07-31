# Base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# Set working directory
WORKDIR /carRoute

# Install system dependencies (including wkhtmltopdf and dependencies)
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create necessary folders
RUN mkdir -p /carRoute/temp_uploads /carRoute/temp_session

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and env files
COPY . .
COPY *.env .

# Expose the app port
EXPOSE 8080

# Run the app with Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "main:app"]
