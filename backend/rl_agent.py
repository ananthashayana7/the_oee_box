import asyncio
import logging
from backend.mqtt_client import mqtt_service

logger = logging.getLogger("rl_agent")

class RLAgent:
    def __init__(self, get_oee_callback):
        self.running = False
        self.get_oee = get_oee_callback
        self.target_topic = "factory/line1/machine1/command"

    async def start(self):
        self.running = True
        logger.info("RL Agent Activated (Autonomous Mode)")
        try:
            while self.running:
                await asyncio.sleep(10) # Check every 10 seconds

                oee_data = self.get_oee()
                if not oee_data:
                    continue

                oee_val = oee_data.get("oee", 0)
                performance = oee_data.get("performance", 0)

                # Simple Logic: If Performance < 90% and > 0 (Running), Optimize
                if 0 < performance < 90:
                    logger.info(f"RL Agent detected low performance ({performance}%). Optimizing...")
                    mqtt_service.publish(self.target_topic, {"command": "OPTIMIZE", "source": "RL_AGENT"})
        except asyncio.CancelledError:
            logger.info("RL Agent stopped")

    def stop(self):
        self.running = False
