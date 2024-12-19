# Use Python 3.10-slim as the base image
FROM python:3.10-slim

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    GRADIO_SERVER_PORT=8073

# Set the working directory
WORKDIR /app/gradio_ui/
COPY . .

# Install build dependencies (optional but recommended for certain Python libraries)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8073

# Command to run the Gradio app
CMD ["python", "app.py"]
