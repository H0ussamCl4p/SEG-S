import paho.mqtt.client as mqtt
import time
import json
import random
import math
import os

BROKER = os.getenv("MQTT_BROKER", "localhost")
TOPIC = "factory/plc/data"
client = mqtt.Client()
client.connect(BROKER, 1883, 60)

print("🏭 Simulating 2 Equipment with Different States...")
print("=" * 80)
print("🔴 MACHINE_002 (Conveyor Belt): ANOMALY State (Critical Vibration + Overheating)")
print("⚠️  MACHINE_003 (Industrial Motor): WARNING → ANOMALY (Temperature Spikes)")
print("=" * 80)

tick = 0
spike_cycle = 0  # For MACHINE_003 temperature spikes

# Equipment configurations
equipment = {
    "MACHINE_002": {
        "name": "Conveyor Belt",
        "type": "anomaly_state",
        "base_vib": 90,  # Critical vibration → ANOMALY
        "base_temp": 78,  # High temperature
        "variation": 8
    },
    "MACHINE_003": {
        "name": "Industrial Motor",
        "type": "warning_with_spikes",
        "base_vib": 65,  # Moderate-high vibration
        "base_temp": 60,  # Starts at WARNING level
        "variation": 5
    }
}

def generate_machine_002_data(tick):
    """MACHINE_002: Critical ANOMALY state - bearing failure with overheating"""
    # Critical vibration range (85-100) with erratic behavior
    vibration = 92 + random.uniform(-10, 10) + math.sin(tick * 0.3) * 8
    vibration = max(80, min(120, vibration))  # Keep in critical range
    
    # High temperature indicating bearing failure
    temp = 82 + random.uniform(-5, 5) + math.cos(tick * 0.2) * 3
    temp = max(75, min(95, temp))  # Critical temperature
    
    # Humidity variation due to heat
    humidity = 35 + random.uniform(-8, 8)
    
    state = "🔴 ANOMALY"
    
    return {
        "timestamp": time.time(),
        "machine_id": "MACHINE_002",
        "equipment_name": "Conveyor Belt",
        "vibration": round(vibration, 2),
        "temperature": round(temp, 2),
        "humidity": round(max(0, min(100, humidity)), 2)
    }, state

def generate_machine_003_data(tick, spike_cycle):
    """MACHINE_003: WARNING with periodic temperature spikes → ANOMALY"""
    # Moderate-high vibration (WARNING level)
    vibration = 68 + random.uniform(-5, 5) + math.sin(tick * 0.15) * 4
    
    # Temperature with periodic spikes every ~30 seconds
    base_temp = 62
    if spike_cycle % 30 < 5:  # Spike for 5 seconds every 30 seconds
        temp = base_temp + 18 + random.uniform(0, 5)  # Temperature spike to ANOMALY
        state = "🔴 ANOMALY"
    else:
        temp = base_temp + random.uniform(-3, 3) + math.cos(tick * 0.1) * 2
        if vibration > 70 or temp > 68:
            state = "🟡 WARNING"
        else:
            state = "🟢 NORMAL"
    
    humidity = 55 + random.uniform(-4, 4)
    
    return {
        "timestamp": time.time(),
        "machine_id": "MACHINE_003",
        "equipment_name": "Industrial Motor",
        "vibration": round(vibration, 2),
        "temperature": round(temp, 2),
        "humidity": round(max(0, min(100, humidity)), 2)
    }, state

try:
    while True:
        # Generate data for 2 machines
        data_002, state_002 = generate_machine_002_data(tick)
        data_003, state_003 = generate_machine_003_data(tick, spike_cycle)
        
        # Publish both
        client.publish(TOPIC, json.dumps(data_002))
        client.publish(TOPIC, json.dumps(data_003))
        
        # Display status
        print(f"\n⏱️  Time: {tick}s | Spike Cycle: {spike_cycle % 30}")
        print(f"  {state_002} MACHINE_002: Vib={data_002['vibration']:.1f} Temp={data_002['temperature']:.1f}°C Hum={data_002['humidity']:.1f}%")
        print(f"  {state_003} MACHINE_003: Vib={data_003['vibration']:.1f} Temp={data_003['temperature']:.1f}°C Hum={data_003['humidity']:.1f}%")
        
        spike_cycle += 1
        tick += 1
        time.sleep(1)

except KeyboardInterrupt:
    print("\n\n✋ Simulation stopped.")
    client.disconnect()
