import paho.mqtt.client as mqtt
import joblib
import json
import numpy as np
import os
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

try:
    print(f"🔌 Connecting to MQTT broker: {BROKER}...")
    client.connect(BROKER, 1883, 60)
    client.subscribe(TOPIC)
    print(f"✅ Subscribed to topic: {TOPIC}")
    print("🎧 Listening for sensor data...")
    client.loop_forever()
except ConnectionRefusedError:
    print(f"❌ Error: Could not connect to MQTT broker at {BROKER}")
except Exception as e:
    print(f"❌ MQTT Error: {e}")
except KeyboardInterrupt:
    print("\n🛑 Stopping Detector.")
