"""Run both simulators in one container:
  - simulate_wear.py : machine telemetry -> MQTT (main dashboard)
  - simulate_esp.py  : fake ESP32 motor telemetry -> ai-engine HTTP (Motor Telemetry page)
If either exits, terminate the other so the container restarts cleanly.
"""
import subprocess
import sys
import time

procs = [
    subprocess.Popen([sys.executable, "-u", "simulate_wear.py"]),
    subprocess.Popen([sys.executable, "-u", "simulate_esp.py"]),
    subprocess.Popen([sys.executable, "-u", "simulate_signal.py"]),
]

try:
    while True:
        for p in procs:
            if p.poll() is not None:
                # one died -> stop the rest and let the orchestrator restart us
                for q in procs:
                    if q.poll() is None:
                        q.terminate()
                sys.exit(1)
        time.sleep(2)
except KeyboardInterrupt:
    for p in procs:
        p.terminate()
