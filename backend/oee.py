import time

class OEECalculator:
    def __init__(self):
        self.start_time = time.time()
        self.run_time = 0.0
        self.last_update = time.time()
        self.state_key = None
        self.count_key = None
        self.start_count = None
        self.ideal_cycle_time = 1.0 # 1 second per part (High speed machine!)

    def update(self, schema, data):
        current_time = time.time()
        dt = current_time - self.last_update
        self.last_update = current_time

        # Re-validate keys against current schema
        if self.state_key and schema.get(self.state_key) != "State":
             self.state_key = None

        if self.count_key and schema.get(self.count_key) != "Counter":
             self.count_key = None

        # Auto-detect keys if not set
        if not self.state_key:
            for k, v in schema.items():
                if v == "State":
                    self.state_key = k
                    break

        if not self.count_key:
            for k, v in schema.items():
                if v == "Counter" and "time" not in k.lower():
                    self.count_key = k
                    break

        # Calculate Availability
        # Availability = Run Time / Total Time
        # We need to integrate Run Time.
        if self.state_key and self.state_key in data:
            state_val = data[self.state_key]
            # Assume 1 is running.
            # In real world, we might map State Code -> Meaning via config
            if state_val == 1:
                self.run_time += dt

        total_time = current_time - self.start_time
        availability = (self.run_time / total_time) if total_time > 0 else 0.0

        # Calculate Performance
        produced_in_session = 0
        if self.count_key and self.count_key in data:
            current_count = data[self.count_key]
            if self.start_count is None:
                self.start_count = current_count

            produced_in_session = current_count - self.start_count

        # Performance = (Produced * Ideal Cycle Time) / Run Time
        performance = 0.0
        if self.run_time > 1.0: # Avoid division by zero or noise at start
            performance = (produced_in_session * self.ideal_cycle_time) / self.run_time
            # Cap at 120% just in case ideal cycle time is wrong
            if performance > 1.2: performance = 1.2

        # Quality (Assume 100% for now)
        quality = 1.0

        oee = availability * performance * quality

        return {
            "availability": round(availability * 100, 1),
            "performance": round(performance * 100, 1),
            "quality": round(quality * 100, 1),
            "oee": round(oee * 100, 1)
        }
