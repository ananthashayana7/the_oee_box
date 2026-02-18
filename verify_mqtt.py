import paho.mqtt.client as mqtt
import time
import json
import sys

BROKER = "127.0.0.1"
PORT = 1883
TOPIC = "factory/line1/machine1/data"

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("Verifier connected to broker")
        client.subscribe(TOPIC)
    else:
        print(f"Verifier failed to connect, return code {rc}")
        sys.exit(1)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print(f"Verifier received: {payload}")
        # Just exit successfully after one message
        sys.exit(0)
    except Exception as e:
        print(f"Verifier error: {e}")
        sys.exit(1)

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(BROKER, PORT, 60)
except Exception as e:
    print(f"Verifier could not connect: {e}")
    sys.exit(1)

client.loop_start()

print("Verifier waiting for messages...")
time.sleep(10) # Wait 10 seconds for a message
print("Verifier timed out waiting for messages.")
sys.exit(1)
