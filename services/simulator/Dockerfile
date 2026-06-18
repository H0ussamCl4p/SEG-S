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
COPY simulate_wear.py simulate_esp.py simulate_signal.py run.py ./

# Run both simulators (machine telemetry over MQTT + fake ESP32 motor telemetry over HTTP)
CMD ["python", "-u", "run.py"]
