# Use Python 3.11 slim image for smaller size and better performance
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies needed for audio processing and other features
RUN apt-get update && apt-get install -y \
    # Build essentials for some Python packages
    build-essential \
    # For audio processing (if needed for voice features)
    ffmpeg \
    # For SSL certificates
    ca-certificates \
    # For downloading files
    curl \
    # Clean up to reduce image size
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user for security
RUN groupadd -r chatbot && useradd -r -g chatbot chatbot

# Copy source code
COPY src/ ./src/
COPY run.py .

# Create directory for temporary files and set ownership
RUN mkdir -p /app/.tmp && chown -R chatbot:chatbot /app

# Switch to non-root user
USER chatbot

# Expose the port the app runs on
EXPOSE 8080

# Add health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Default command to run the application
CMD ["python", "run.py"]

# Production stage
FROM base AS production

# Set production environment
ENV ENVIRONMENT=production

# Use uvicorn directly for better production performance
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]

# Development stage
FROM python:3.11-slim AS development

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    ENVIRONMENT=development \
    LOG_LEVEL=debug

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    ffmpeg \
    ca-certificates \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements and install dependencies (including dev dependencies)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install development dependencies as root
RUN pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    "httpx[testing]" \
    black \
    flake8

# Create a non-root user for security
RUN groupadd -r chatbot && useradd -r -g chatbot chatbot

# Copy source code
COPY src/ ./src/
COPY run.py .

# Create directory for temporary files and set ownership
RUN mkdir -p /app/.tmp && chown -R chatbot:chatbot /app

# Switch to non-root user
USER chatbot

# Expose the port the app runs on
EXPOSE 8080

# Enable hot reloading for development
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
