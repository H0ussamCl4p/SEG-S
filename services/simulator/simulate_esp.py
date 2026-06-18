"""
Fake ESP32 motor-telemetry simulator.

Replaces a physical ESP32 board: POSTs realistic motor readings (thermocouple,
ambient temp, humidity, vibration) to the ai-engine's /api/esp/ingest endpoint,
driving the exact same pipeline (command logic, InfluxDB esp_motor, MTTF model)
that a real board would. Powers the "Motor Telemetry" dashboard page.

Runs a repeating cycle so the page shows dynamic behaviour:
  nominal (warm, safe)  ->  load spike (warn/critical, motor slows/stops)  ->  cooldown
"""
import json
import math
import os
import random
import time
import urllib.request

AI_ENGINE_URL = os.getenv("AI_ENGINE_URL", "http://ai-engine:8000").rstrip("/")
INGEST_URL = f"{AI_ENGINE_URL}/api/esp/ingest"
DEVICE_ID = os.getenv("ESP_DEVICE_ID", "esp32_sim_motor")
INTERVAL = float(os.getenv("ESP_SIM_INTERVAL", "2"))

# Phase plan (seconds) — one full cycle, then repeat.
NOMINAL_S = float(os.getenv("ESP_NOMINAL_S", "150"))   # warm but safe
LOAD_S = float(os.getenv("ESP_LOAD_S", "90"))          # overload -> warn/critical
COOLDOWN_S = float(os.getenv("ESP_COOLDOWN_S", "75"))  # recovery
CYCLE_S = NOMINAL_S + LOAD_S + COOLDOWN_S

# Targets per phase: (thermocouple_C, vibration)
TARGETS = {
    "nominal":  (62.0, 34.0),   # below warn (70C / vib 60)
    "load":     (92.0, 74.0),   # above critical (85C) and vib warn*1.5
    "cooldown": (45.0, 32.0),
}


def phase_for(elapsed: float) -> str:
    p = elapsed % CYCLE_S
    if p < NOMINAL_S:
        return "nominal"
    if p < NOMINAL_S + LOAD_S:
        return "load"
    return "cooldown"


def post(payload: dict) -> None:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        INGEST_URL, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        resp.read()


def main() -> None:
    print(f"🔧 Fake ESP motor simulator -> {INGEST_URL} (device={DEVICE_ID})", flush=True)
    # Start near ambient so the thermal model sees a real heating curve.
    thermo = 30.0
    vib = 33.0
    start = time.time()
    tick = 0
    while True:
        elapsed = time.time() - start
        phase = phase_for(elapsed)
        t_target, v_target = TARGETS[phase]

        # First-order easing toward the phase target -> smooth heat-up/cool-down
        # curves the backend's exponential MTTF fit can work with.
        ease = 0.05
        thermo += (t_target - thermo) * ease + random.uniform(-0.4, 0.4)
        vib += (v_target - vib) * ease + random.uniform(-1.2, 1.2)

        ambient = 26.0 + math.sin(tick * 0.02) * 1.5 + random.uniform(-0.3, 0.3)
        humidity = 45.0 + math.sin(tick * 0.015) * 4 + random.uniform(-1.5, 1.5)

        payload = {
            "device_id": DEVICE_ID,
            "thermocouple": round(thermo, 2),
            "temperature": round(ambient, 2),
            "humidity": round(max(0.0, min(100.0, humidity)), 2),
            "vibration": round(max(0.0, vib), 2),
        }
        try:
            post(payload)
            if tick % 5 == 0:
                print(f"[{phase:8}] motor={payload['thermocouple']}C vib={payload['vibration']} "
                      f"amb={payload['temperature']}C hum={payload['humidity']}%", flush=True)
        except Exception as e:
            # ai-engine may still be starting — keep trying.
            if tick % 5 == 0:
                print(f"⚠️  ESP post failed ({e}); retrying...", flush=True)

        tick += 1
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
