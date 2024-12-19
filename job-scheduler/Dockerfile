# Use Python 3.10-slim as the base image
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    supervisor \
    redis-server \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory to /app
WORKDIR /app/job-scheduler/
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the necessary ports for Redis (or FastAPI if used)
EXPOSE 5050

# Start Redis, FastAPI, and Celery together using Supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]