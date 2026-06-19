import paho.mqtt.client as mqtt
import joblib
import json
import numpy as np
import os
import time
import pandas as pd # Added for timestamp handling
from influxdb import InfluxDBClient

# --- CONFIGURATION ---
BROKER = os.getenv("MQTT_BROKER", "localhost")
TOPIC = "factory/plc/data"
MODEL_FILE = "/app/models/anomaly_model.pkl"  # Use new trained model
SCALER_FILE = "scaler.pkl"
LOG_FILE = "live_data.csv" # The file where we save history for the dashboard

# InfluxDB Configuration
INFLUX_HOST = os.getenv("INFLUX_HOST", "localhost")
INFLUX_PORT = int(os.getenv("INFLUX_PORT", "8086"))
INFLUX_DB = os.getenv("INFLUX_DB", "factory_data")

# Expected operating maxima for the heuristic fallback score (used when no ML
# model is loaded). Configurable so they can track real equipment limits.
EXPECTED_MAX_VIBRATION = float(os.getenv("EXPECTED_MAX_VIBRATION", "120"))
EXPECTED_MAX_TEMPERATURE = float(os.getenv("EXPECTED_MAX_TEMPERATURE", "95"))


def heuristic_score(vibration, temperature):
    """Anomaly score in [-1, 1] derived from vibration/temperature when no ML
    model is available. Mirrors the ai-engine API's estimate_score so the stored
    ai_score is meaningful — it drives dashboard uptime, alerts and RUL. Higher
    vibration/temperature => lower (worse) score."""
    try:
        vib_norm = min(max(vibration / EXPECTED_MAX_VIBRATION, 0.0), 1.0) if EXPECTED_MAX_VIBRATION > 0 else 0.0
        temp_norm = min(max(temperature / EXPECTED_MAX_TEMPERATURE, 0.0), 1.0) if EXPECTED_MAX_TEMPERATURE > 0 else 0.0
        impact = 0.6 * vib_norm + 0.4 * temp_norm
        return float(max(-1.0, min(1.0, 1.0 - 2.0 * impact)))
    except Exception:
        return 0.0

# --- INITIALIZATION ---
# 1. Load the AI (if available)
model = None
scaler = None
model_columns = None

if os.path.exists(MODEL_FILE):
    print(f"🧠 Loading AI Model from {MODEL_FILE}...")
    try:
        import pickle
        with open(MODEL_FILE, 'rb') as f:
            model_data = pickle.load(f)
        
        # Handle both old and new model formats
        if isinstance(model_data, dict):
            model = model_data.get('model')
            scaler = model_data.get('scaler')
            model_columns = model_data.get('columns', ['vibration', 'temperature'])
        else:
            model = model_data
            scaler = None
            model_columns = ['vibration', 'temperature']
            
        print("✅ AI Model loaded successfully")
        print(f"   Features: {model_columns}")
    except Exception as e:
        print(f"⚠️  Warning: Could not load model: {e}")
        model = None
        scaler = None
else:
    print("ℹ️  No AI model found. Data will be collected without predictions.")
    print(f"   Expected path: {MODEL_FILE}")

# 2. Connect to InfluxDB
print("📊 Connecting to InfluxDB...")
try:
    influx_client = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT)
    influx_client.switch_database(INFLUX_DB)
    print(f"✅ Connected to InfluxDB: {INFLUX_DB}")
except Exception as e:
    print(f"⚠️  Warning: Could not connect to InfluxDB: {e}")
    influx_client = None

# 2. Setup the Log File (Create headers if file doesn't exist)
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w") as f:
        f.write("timestamp,vibration,temperature,score,status\n")

print(f"✅ AI Ready. Logging data to {LOG_FILE}...")

# --- CORE LOGIC ---
def on_message(client, userdata, msg):
    try:
        # 1. Parse Data
        payload = json.loads(msg.payload.decode())
        vib = payload['vibration']
        temp = payload['temperature']
        hum = payload.get('humidity', None)
        machine_id = payload.get('machine_id', 'UNKNOWN')
        equipment_name = payload.get('equipment_name', machine_id)
        
        # 2. Pre-process and Predict (if model available)
        status = "NORMAL"
        score = 0.0
        
        if model is not None:
            try:
                features = np.array([[vib, temp]])
                
                # DON'T scale - model was trained on different features!
                # The MQTT data has vibration+temp, but model was trained on Humidity+Age+etc
                # So we use the raw features directly
                features_scaled = features
                
                # 3. Predict (Isolation Forest returns -1 for anomaly, 1 for normal)
                prediction = model.predict(features_scaled)
                raw_score = model.score_samples(features_scaled)[0]
                
                # Convert to 0-1 scale (higher is better)
                score = (raw_score + 0.5) * 2  # Normalize roughly to 0-1
                
                # 4. Determine Status
                if prediction[0] == -1: 
                    status = "ANOMALY"
                elif score < 0.3:  # Lower threshold for warning
                    status = "WARNING"
            except Exception as e:
                print(f"⚠️  Prediction error: {e}")
                status = "NORMAL"
                score = 0.0
        else:
            # No ML model loaded: fall back to a heuristic score so the stored
            # ai_score carries real signal (otherwise it is always 0.0, which
            # makes uptime 0% and every reading a "warning").
            score = heuristic_score(vib, temp)
            if score < -0.5:
                status = "ANOMALY"
            elif score < 0.1:
                status = "WARNING"
            else:
                status = "NORMAL"

        # 5. Output to Terminal (Color Coded per machine)
        color = "\033[92m" if status == "NORMAL" else "\033[93m" if status == "WARNING" else "\033[91m"
        if hum is not None:
            print(f"{color}[{machine_id}] [{status}] Vib: {vib:.2f} | Temp: {temp:.2f} | Hum: {float(hum):.2f} | Score: {score:.4f}\033[0m")
        else:
            print(f"{color}[{machine_id}] [{status}] Vib: {vib:.2f} | Temp: {temp:.2f} | Score: {score:.4f}\033[0m")

        # 6. SAVE TO CSV (Critical for Dashboard) - One file per machine
        log_file = f"live_data_{machine_id}.csv"
        if not os.path.exists(log_file):
            with open(log_file, "w") as f:
                f.write("timestamp,machine_id,vibration,temperature,humidity,score,status\n")
        
        with open(log_file, "a") as f:
            timestamp = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
            if hum is not None:
                f.write(f"{timestamp},{machine_id},{vib},{temp},{hum},{score},{status}\n")
            else:
                f.write(f"{timestamp},{machine_id},{vib},{temp},,{score},{status}\n")
        
        # 7. SAVE TO INFLUXDB (For Grafana) - with machine_id tag
        if influx_client:
            try:
                json_body = [
                    {
                        "measurement": "machine_telemetry",
                        "tags": {
                            "machine_id": machine_id,
                            "equipment_name": equipment_name,
                            "status": status
                        },
                        "fields": {
                            "vibration": float(vib),
                            "temperature": float(temp),
                            **({"humidity": float(hum)} if hum is not None else {}),
                            "ai_score": float(score)
                        }
                    }
                ]
                influx_client.write_points(json_body)
            except Exception as influx_error:
                print(f"⚠️  InfluxDB write error: {influx_error}")
            
    except Exception as e:
        print(f"Error processing message: {e}")

# --- MQTT CONNECTION ---
# Using legacy API for paho-mqtt 1.6.1 compatibility
client = mqtt.Client()
client.on_message = on_message


# Subscribe inside on_connect so the subscription is re-established on every
# (re)connect. paho's loop_forever auto-reconnects the TCP socket after a broker
# restart, but it does NOT re-subscribe automatically — without this the consumer
# silently stops receiving data after any broker blip.
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe(TOPIC)
        print(f"✅ Connected & subscribed to topic: {TOPIC}")
        print("🎧 Listening for sensor data...")
    else:
        print(f"❌ MQTT connect failed (rc={rc})")


client.on_connect = on_connect

# Back off and retry automatically instead of exiting on transient broker outages.
client.reconnect_delay_set(min_delay=1, max_delay=30)

while True:
    try:
        print(f"🔌 Connecting to MQTT broker: {BROKER}...")
        client.connect(BROKER, 1883, 60)
        client.loop_forever()  # blocks; auto-reconnects + re-fires on_connect
    except KeyboardInterrupt:
        print("\n🛑 Stopping Detector.")
        break
    except Exception as e:
        print(f"❌ MQTT connection error: {e} — retrying in 5s...")
        time.sleep(5)
