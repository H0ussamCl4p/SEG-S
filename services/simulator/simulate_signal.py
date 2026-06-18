"""
Raw vibration-waveform simulator for FFT / envelope / bearing-fault analysis.

Unlike the scalar machine simulator, this emits a full high-frequency vibration
window (2048 samples @ 10 kHz) and POSTs it to /api/signal/ingest. It cycles:
    healthy  ->  bearing outer-race fault (BPFO), severity ramping up  ->  repeat
so the "Signal Analysis" page shows kurtosis/crest-factor rising and a BPFO peak
appearing in the envelope spectrum — exactly what real condition monitoring sees.
"""
import json
import os
import time
import urllib.request

import numpy as np

AI_ENGINE_URL = os.getenv("AI_ENGINE_URL", "http://ai-engine:8000").rstrip("/")
URL = f"{AI_ENGINE_URL}/api/signal/ingest"
DEVICE_ID = os.getenv("SIGNAL_DEVICE_ID", "bearing_motor_1")

FS = 10000.0          # sample rate (Hz)
N = 2048              # samples per window (~0.2 s)
FR = 25.0             # shaft speed (Hz) = 1500 RPM
FN = 3000.0           # bearing/structural resonance excited by impacts (Hz)
INTERVAL = float(os.getenv("SIGNAL_SIM_INTERVAL", "3"))
HEALTHY_S = float(os.getenv("SIGNAL_HEALTHY_S", "150"))
FAULT_S = float(os.getenv("SIGNAL_FAULT_S", "150"))
CYCLE_S = HEALTHY_S + FAULT_S

# Bearing geometry (matches the backend default) -> BPFO ~= 80 Hz
N_BALLS, D_BALL, D_PITCH = 8, 8.0, 40.0


def bpfo() -> float:
    ratio = D_BALL / D_PITCH
    return (N_BALLS / 2.0) * FR * (1.0 - ratio)


def make_window(faulty: bool, severity: float) -> np.ndarray:
    t = np.arange(N) / FS
    # Shaft harmonics (always present) + broadband noise
    x = (0.5 * np.sin(2 * np.pi * FR * t)
         + 0.2 * np.sin(2 * np.pi * 2 * FR * t)
         + 0.1 * np.sin(2 * np.pi * 3 * FR * t)
         + 0.15 * np.random.randn(N))
    if faulty and severity > 0:
        f = bpfo()
        period = 1.0 / f
        # Impulse train at BPFO with small random slip
        impulse = np.zeros(N)
        k = 0
        while k * period < t[-1]:
            jitter = np.random.uniform(-0.0004, 0.0004)
            idx = int(round((k * period + jitter) * FS))
            if 0 <= idx < N:
                impulse[idx] = 1.0
            k += 1
        # Each impact rings the resonance (decaying sinusoid at FN)
        td = np.arange(int(0.005 * FS)) / FS
        kernel = np.exp(-td * 800.0) * np.sin(2 * np.pi * FN * td)
        resp = np.convolve(impulse, kernel)[:N]
        x = x + severity * resp
    return x


def main() -> None:
    print(f"📈 Raw vibration simulator -> {URL} (BPFO≈{bpfo():.0f} Hz)", flush=True)
    start = time.time()
    while True:
        phase = (time.time() - start) % CYCLE_S
        faulty = phase >= HEALTHY_S
        # Ramp severity through the fault phase so degradation is visible
        severity = 0.0 if not faulty else min(2.5, 0.6 + (phase - HEALTHY_S) / FAULT_S * 2.0)
        x = make_window(faulty, severity)
        payload = {
            "device_id": DEVICE_ID,
            "fs": FS,
            "shaft_hz": FR,
            "condition": "bearing_fault" if faulty else "healthy",
            "samples": [round(float(v), 5) for v in x],
        }
        try:
            req = urllib.request.Request(
                URL, data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"}, method="POST",
            )
            with urllib.request.urlopen(req, timeout=8) as r:
                r.read()
            print(f"sent: {'FAULT sev=%.1f' % severity if faulty else 'healthy'}", flush=True)
        except Exception as e:
            print(f"⚠️  signal post failed ({e}); retrying...", flush=True)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
