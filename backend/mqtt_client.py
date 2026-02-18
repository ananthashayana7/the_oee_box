import paho.mqtt.client as mqtt
import asyncio
import json
import logging
import os

logger = logging.getLogger("mqtt_client")

class MQTTClient:
    def __init__(self, broker_host=None, broker_port=1883):
        if broker_host is None:
            broker_host = os.getenv("BROKER_HOST", "127.0.0.1")
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.connected = False
        self.message_callback = None

    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            logger.info("Connected to MQTT Broker")
            self.connected = True
            client.subscribe("#")
        else:
            logger.error(f"Failed to connect, return code {rc}")

    def on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = msg.payload.decode()
            logger.debug(f"Received message on {topic}: {payload}")
            if self.message_callback:
                # Run the callback in the event loop
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(self.message_callback(topic, payload))
                except RuntimeError:
                    # If no loop is running (e.g. testing), just call it if synchronous?
                    # But message_callback is expected to be async.
                    # This happens inside paho thread, so we need to be careful.
                    # Actually, paho callbacks run in a separate thread.
                    # To call async function, we need to schedule it in the main loop.
                    # But we don't have easy access to the main loop here unless we pass it.
                    pass
                    # For now, let's assume we can get the loop from main thread if we are careful,
                    # or better: Use run_coroutine_threadsafe if we have the loop.

        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def set_loop(self, loop):
        self.loop = loop

    def on_message_safe(self, client, userdata, msg):
        # Thread-safe version
        try:
            topic = msg.topic
            payload = msg.payload.decode()
            if self.message_callback and hasattr(self, 'loop'):
                asyncio.run_coroutine_threadsafe(self.message_callback(topic, payload), self.loop)
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def start(self, loop=None):
        if loop:
            self.loop = loop
            self.client.on_message = self.on_message_safe

        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"Could not connect to broker: {e}")

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

    def publish(self, topic, message):
        if isinstance(message, dict):
            message = json.dumps(message)
        self.client.publish(topic, message)

mqtt_service = MQTTClient()
