import logging
import random

logger = logging.getLogger("copilot")

class ChatAgent:
    def __init__(self):
        self.responses = {
            "hello": ["Hello! How can I assist you with the machine today?", "Greetings, operator."],
            "status": ["The machine is currently {state}.", "Current operational status: {state}."],
            "oee": ["The OEE is currently {oee}%. Availability: {availability}%, Performance: {performance}%, Quality: {quality}%."],
            "fault": ["There are no active faults reported.", "System is healthy."],
            "stop": ["To stop the machine, use the 'STOP' button in the control panel or type 'STOP'."],
            "optimize": ["I can optimize the machine settings. Sending 'OPTIMIZE' command will adjust parameters."],
            "default": ["I'm not sure about that. Try asking about 'status', 'OEE', or 'faults'."]
        }

    def process_query(self, query: str, context: dict) -> str:
        """
        Process a natural language query using simple keyword matching and context injection.
        context: {
            "oee": {...},
            "data": {...},
            "schema": {...}
        }
        """
        query = query.lower()

        # Extract context
        oee_data = context.get("oee", {})
        sensor_data = context.get("data", {})

        # Determine current state text
        state_code = sensor_data.get("state_code", 0)
        state_map = {0: "STOPPED", 1: "RUNNING", 2: "FAULT"}
        current_state = state_map.get(state_code, "UNKNOWN")

        # Logic
        if "hello" in query or "hi" in query:
            return random.choice(self.responses["hello"])

        if "status" in query or "state" in query or "doing" in query:
            return random.choice(self.responses["status"]).format(state=current_state)

        if "oee" in query or "performance" in query or "efficiency" in query:
            return random.choice(self.responses["oee"]).format(
                oee=oee_data.get("oee", 0),
                availability=oee_data.get("availability", 0),
                performance=oee_data.get("performance", 0),
                quality=oee_data.get("quality", 0)
            )

        if "fault" in query or "error" in query or "problem" in query:
            if state_code == 2:
                return f"ALERT: The machine is in FAULT state (Code 2). Check sensor inputs."
            return random.choice(self.responses["fault"])

        if "stop" in query:
            return random.choice(self.responses["stop"])

        if "optimize" in query:
            return random.choice(self.responses["optimize"])

        # Fallback: Check if user is asking about a specific sensor value
        for key, value in sensor_data.items():
            if key in query:
                return f"The current value of '{key}' is {value}."

        return random.choice(self.responses["default"])
