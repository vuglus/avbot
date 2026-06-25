# Multi-stage build
FROM python:3.9-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

 RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*   

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.9-slim

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app
WORKDIR /home/app

# Copy dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

# Copy application code
COPY . ./avbot
WORKDIR /home/app/avbot

# Expose port
EXPOSE 5200

# Environment variables
ENV DB_PATH=/data/avbot.db
ENV CONFIG_PATH=/config/config.yml
ENV DIALOGS_PATH=/dialogs
ENV YDB_ENDPOINT=grpcs://ydb.serverless.yandexcloud.net:2135
ENV YDB_DATABASE=/ru-central1/b1g83nrkad3n5ern2vc4/etn488o015sncsav0m01

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5200/health || exit 1

# Run application
ENTRYPOINT ["python", "bot.py"]
