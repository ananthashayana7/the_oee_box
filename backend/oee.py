import time
import logging

logger = logging.getLogger("oee_calculator")

class OEECalculator:
    def __init__(self):
        self.start_time = time.time()
        self.last_update_ts = time.time()
        self.run_duration = 0.0 # Time spent in "Running" state
        self.session_duration = 0.0 # Total time since start

        self.state_key = None
        self.count_key = None
        self.start_count = None

        # Configuration (Defaults)
        self.config = {
            "ideal_cycle_time": 1.0, # seconds per part
            "target_availability": 0.9,
            "target_performance": 0.95,
            "target_quality": 0.99
        }

    def set_config(self, config_dict):
        """Update OEE parameters dynamically."""
        if config_dict:
            self.config.update(config_dict)
            logger.info(f"OEE Config Updated: {self.config}")

    def update(self, schema, data):
        current_time = time.time()
        dt = current_time - self.last_update_ts
        self.last_update_ts = current_time

        # Prevent huge jumps if system slept
        if dt > 60: dt = 0

        self.session_duration += dt

        # Auto-Detect Keys if missing
        if not self.state_key:
            for k in schema:
                if "state" in k.lower() or "status" in k.lower():
                    self.state_key = k
                    break

        if not self.count_key:
            for k in schema:
                if "count" in k.lower() or "produced" in k.lower():
                    self.count_key = k
                    break

        # 1. Availability Calculation
        is_running = False
        if self.state_key and self.state_key in data:
            val = data[self.state_key]
            # Heuristic: 1 usually means Running in standard PLCs
            if val == 1 or val == "RUNNING" or val == True:
                is_running = True
                self.run_duration += dt

        availability = 0.0
        if self.session_duration > 0:
            availability = self.run_duration / self.session_duration

        # 2. Performance Calculation
        produced = 0
        if self.count_key and self.count_key in data:
            current_count = data[self.count_key]
            if self.start_count is None:
                self.start_count = current_count

            produced = current_count - self.start_count
            if produced < 0: produced = 0 # Reset handling

        # Performance = (Ideal Cycle Time * Total Count) / Run Time
        performance = 0.0
        ideal_cycle_time = self.config.get("ideal_cycle_time", 1.0)

        if self.run_duration > 1.0:
            performance = (produced * ideal_cycle_time) / self.run_duration

        # Cap performance to avoid 5000% on bad config
        if performance > 1.5: performance = 1.5

        # 3. Quality (Mock for now, assume 100% unless 'rejects' key exists)
        quality = 1.0
        rejects = 0
        # Try to find reject key
        for k in data:
            if "reject" in k.lower() or "bad" in k.lower():
                rejects = data[k]
                break

        if produced > 0:
            quality = (produced - rejects) / produced

        oee = availability * performance * quality

        return {
            "availability": round(availability * 100, 1),
            "performance": round(performance * 100, 1),
            "quality": round(quality * 100, 1),
            "oee": round(oee * 100, 1),
            "trust": 1.0, # Placeholder, overwritten by sanitizer
            "targets": {
                "availability": self.config.get("target_availability"),
                "performance": self.config.get("target_performance"),
                "quality": self.config.get("target_quality")
            }
        }
