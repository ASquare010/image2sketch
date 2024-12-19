FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app/
COPY . .

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-venv \
    python3-pip \
    git \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Git LFS
RUN wget -q https://packagecloud.io/github/git-lfs/gpgkey -O- | gpg --dearmor > /usr/share/keyrings/git-lfs-archive-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/git-lfs-archive-keyring.gpg] https://packagecloud.io/github/git-lfs/ubuntu/ jammy main" | tee /etc/apt/sources.list.d/git-lfs.list \
    && apt-get update && apt-get install -y git-lfs && git lfs install

# Clone repositories into the desired directory
RUN git clone https://huggingface.co/sharazAhm890/image2sketch /app/src/ --depth 1
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

# Run the Flask app with Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]