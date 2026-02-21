import paho.mqtt.client as mqtt
import json
import time
import random

BROKER = "127.0.0.1"
PORT = 1883

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("Connected to MQTT Broker")
    else:
        print(f"Failed to connect, return code {rc}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.connect(BROKER, PORT, 60)
client.loop_start()

machines = [
    {
        "id": "machine_1",
        "topic": "factory/line1/machine_1/data",
        "data": {"count": 100, "state_code": 1, "temp": 45.5}
    },
    {
        "id": "machine_process",
        "topic": "factory/line1/machine_process/data",
        "data": {"pressure_psi": 120.5, "flow_gpm": 34.2, "ph_level": 7.1}
    },
    {
        "id": "machine_vibe",
        "topic": "factory/line1/machine_vibe/data",
        "data": {"vibration_x": 0.04, "vibration_y": 0.02, "rms_velocity": 0.15}
    },
    {
        "id": "machine_pack",
        "topic": "factory/line1/machine_pack/data",
        "data": {"bottles_filled": 5000, "rejects": 12, "conveyor_speed": 1.5}
    },
    {
        "id": "machine_env",
        "topic": "factory/line1/machine_env/data",
        "data": {"humidity_pct": 55, "lux": 450, "co2_ppm": 800}
    }
]

print("Starting Heterogeneity Simulation (60 seconds)...")

for i in range(60):
    for m in machines:
        payload = m["data"].copy()

        # Simulate dynamic values
        for k, v in payload.items():
            if isinstance(v, (int, float)):
                if "count" in k or "filled" in k:
                    payload[k] += random.randint(0, 5) # Monotonic increase
                else:
                    payload[k] += random.uniform(-0.5, 0.5) # Oscillation

        payload["timestamp"] = time.time()

        client.publish(m["topic"], json.dumps(payload))

    time.sleep(1)

client.loop_stop()
client.disconnect()
print("Simulation Complete.")
