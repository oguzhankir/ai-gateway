# Multi-stage build for backend
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Note: spaCy models will be downloaded lazily on first use via nlp_models.py
# The code has fallback mechanisms for smaller models if large ones are unavailable

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Make scripts executable
RUN chmod +x scripts/*.sh

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python scripts/healthcheck.py || exit 1

# Expose port
EXPOSE 8000

# Run initialization script then start server
CMD ["sh", "-c", "./scripts/init.sh && uvicorn app.main:app --host 0.0.0.0 --port 8000"]

