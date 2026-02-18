import logging

logger = logging.getLogger("gatekeeper")

class CommandGatekeeper:
    def __init__(self):
        self.allowed_commands = ["START", "STOP", "RESET", "OPTIMIZE"]
        self.allowed_topics = ["factory/line1/machine1/command"]

    def validate(self, command: str, target: str) -> bool:
        if command not in self.allowed_commands:
            logger.warning(f"Command '{command}' denied: Not in allowlist")
            return False

        # In a real system, we might use regex for topics
        if target not in self.allowed_topics:
            logger.warning(f"Target '{target}' denied: Not in allowlist")
            return False

        return True
