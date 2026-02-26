import asyncio
import logging
import asyncio
from backend.mqtt_client import mqtt_service
from backend.database import db_manager

logger = logging.getLogger("rl_agent")

class RLAgent:
    def __init__(self, get_oee_callback, mode="shadow"):
        self.running = False
        self.get_oee = get_oee_callback
        self.target_topic = "factory/line1/machine1/command"
        self.mode = mode

    async def start(self):
        self.running = True
        logger.info(f"RL Agent Activated (Mode: {self.mode})")
        try:
            while self.running:
                await asyncio.sleep(10) # Check every 10 seconds

                oee_data = self.get_oee()
                if not oee_data:
                    continue

                oee_val = oee_data.get("oee", 0)
                performance = oee_data.get("performance", 0)
                trust_score = oee_data.get("trust", 1.0) # Assume high trust if not provided

                # Safety Check
                if trust_score < 0.8:
                    if self.mode != "shadow": # Log only if we are supposed to be active but are blocked
                         logger.warning(f"Optimization Blocked: Low Trust Score ({trust_score})")
                    continue

                # Simple Logic: If Performance < 90% and > 0 (Running), Optimize
                if 0 < performance < 90:
                    action = "OPTIMIZE"
                    details = f"Low performance ({performance}%). Triggering optimization."

                    if self.mode == "shadow":
                        logger.info(f"[SHADOW] Would execute: {action} - {details}")
                        await db_manager.log_audit("AI_SHADOW", "RL_AGENT", details)
                    else:
                        logger.info(f"Executing: {action}")
                        mqtt_service.publish(self.target_topic, {"command": action, "source": "RL_AGENT"})
                        await db_manager.log_audit("AI_ACTION", "RL_AGENT", details)

        except asyncio.CancelledError:
            logger.info("RL Agent stopped")

    def stop(self):
        self.running = False
