# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr for real-time logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies if required for network/certificates
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application source code
COPY console/ ./console/
COPY src/ ./src/

# Default container configuration
# Railway automatically sets PORT (e.g., 8080) and CONSOLE_HOST defaults to 0.0.0.0 when PORT is present.
ENV PORT=8080

EXPOSE 8080

# Health check using the unauthenticated /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Start the console backend server
CMD ["python3", "-m", "console.backend.server"]
