import logging
from backend.database import db_manager

logger = logging.getLogger("alert_engine")

class AlertEngine:
    def __init__(self):
        self.last_fault_time = 0
        self.last_temp_alert_time = 0
        self.cooldown = 60 # seconds

    async def process(self, data):
        timestamp = data.get("timestamp", 0)

        # Rule 1: Machine Fault
        if data.get("state_code") == 2:
            if timestamp - self.last_fault_time > self.cooldown:
                message = "CRITICAL: Machine reported FAULT state (Code 2)"
                logger.warning(message)
                await db_manager.create_alert(message, severity="error")
                self.last_fault_time = timestamp

        # Rule 2: High Temperature
        temp = data.get("temperature")
        if temp and temp > 90:
            if timestamp - self.last_temp_alert_time > self.cooldown:
                message = f"WARNING: High Temperature detected ({temp}°C)"
                logger.warning(message)
                await db_manager.create_alert(message, severity="warning")
                self.last_temp_alert_time = timestamp

alert_engine = AlertEngine()
