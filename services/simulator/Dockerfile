# ==========================================
# Simulator Dockerfile (Speed Optimized)
# Target: <5s incremental, <30s clean build
# ==========================================

FROM python:3.10-slim

WORKDIR /app

# Copy requirements first (changes rarely)
COPY requirements.txt .

# Use BuildKit cache mount for pip
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-compile -r requirements.txt

# Copy simulator code
COPY simulate_wear.py .

# Run the simulator
CMD ["python", "simulate_wear.py"]
