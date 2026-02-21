from backend.oee import OEECalculator

class MachineState:
    def __init__(self, machine_id):
        self.id = machine_id
        self.latest_data = {}
        self.schema = {}
        self.oee = OEECalculator()
        self.status = "OFFLINE"
        self.last_seen = 0

    def process_data(self, data):
        self.latest_data = data
        # ... logic to update schema, oee ...
        # (Simplified for now, as machine_manager.py handles the heavy lifting)
