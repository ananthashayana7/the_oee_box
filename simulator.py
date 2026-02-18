import paho.mqtt.client as mqtt
import time
import json
import random
import threading
import sys
import os
import argparse

BROKER = os.getenv("BROKER_HOST", "127.0.0.1")
PORT = 1883
DATA_TOPIC = "factory/line1/machine1/data"
COMMAND_TOPIC = "factory/line1/machine1/command"

# CLI Arguments
parser = argparse.ArgumentParser()
parser.add_argument("--mode", choices=["clean", "dirty", "dumb"], default="clean", help="Simulation mode")
args = parser.parse_args()

# Machine State
state = {
    "production_count": 0,
    "temperature": 40.0,
    "state_code": 1, # 1: Run, 0: Stop, 2: Fault
    "target_speed": 100,
    "current_amps": 0.0 # New sensor for inference
}

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"Simulator connected to broker at {BROKER}:{PORT}")
        client.subscribe(COMMAND_TOPIC)
    else:
        print(f"Simulator failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print(f"Simulator received command: {payload}")

        cmd = payload.get("command")
        if cmd == "STOP":
            state["state_code"] = 0
            print("Simulator: STOPPED")
        elif cmd == "START":
            state["state_code"] = 1
            print("Simulator: STARTED")
        elif cmd == "RESET":
            state["production_count"] = 0
            state["state_code"] = 0
            print("Simulator: RESET")
        elif cmd == "OPTIMIZE":
            print("Simulator: OPTIMIZING SPEED...")
            # Simulate optimization effect
            pass

    except Exception as e:
        print(f"Error processing command: {e}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(BROKER, PORT, 60)
except Exception as e:
    print(f"Could not connect to broker: {e}")
    sys.exit(1)

client.loop_start()

print(f"Simulator started. Publishing to {DATA_TOPIC}")

try:
    while True:
        # Simulate dynamics
        current_temp = state["temperature"]
        if state["state_code"] == 1:
            # Running
            state["production_count"] += 1
            # Random fluctuation around 40-50
            fluctuation = random.uniform(-0.5, 0.5)
            state["temperature"] = max(30, min(90, current_temp + fluctuation))
            state["current_amps"] = random.uniform(10.0, 15.0) # Normal running amps
        elif state["state_code"] == 0:
            # Stopped - temp cools down
            state["temperature"] = max(20, current_temp - 0.1)
            state["current_amps"] = random.uniform(0.0, 0.2) # Idle amps

        # Base Payload
        payload = {
            "timestamp": time.time(),
            "production_count": state["production_count"],
            "temperature": round(state["temperature"], 2),
            "state_code": state["state_code"],
            "current_amps": round(state["current_amps"], 2)
        }

        # Modify based on Mode
        if args.mode == "dumb":
            # Missing state_code, missing production_count
            # Only sends amps and maybe a generic "ch2_val" for count
            payload.pop("state_code", None)
            count = payload.pop("production_count", None)
            payload["ch2_val"] = count # Alias test

        elif args.mode == "dirty":
            # Inject Noise
            if random.random() < 0.1:
                # Spike
                payload["temperature"] = 500.0
                print("SIMULATOR: Injected Temperature Spike (500.0)")

            if random.random() < 0.1:
                # Drop key
                payload.pop("state_code", None)
                print("SIMULATOR: Dropped state_code")

        client.publish(DATA_TOPIC, json.dumps(payload))
        # print(f"Published: {payload}")
        time.sleep(2) # Slow down to trigger low performance (50%)
except KeyboardInterrupt:
    client.loop_stop()
    client.disconnect()
