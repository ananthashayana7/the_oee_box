from backend.schema_inference import SchemaInferenceEngine
from backend.oee import OEECalculator
from backend.sanitizer import DataSanitizer
from backend.virtual_sensors import VirtualSensorFactory

class MachineState:
    def __init__(self, machine_id):
        self.machine_id = machine_id
        self.schema_engine = SchemaInferenceEngine()
        self.oee_calculator = OEECalculator()
        self.sanitizer = DataSanitizer()
        self.virtual_factory = VirtualSensorFactory()
        self.current_data = {}
        self.latest_oee = {"availability": 0, "performance": 0, "quality": 0, "oee": 0, "trust": 1.0}
        self.schema = {}
        self.virtual_keys = []

class MachineManager:
    def __init__(self):
        self.machines = {} # machine_id -> MachineState

    def get_machine(self, machine_id):
        if machine_id not in self.machines:
            self.machines[machine_id] = MachineState(machine_id)
        return self.machines[machine_id]

    def get_all_states(self):
        return {
            mid: {
                "oee": m.latest_oee,
                "data": m.current_data,
                "schema": m.schema,
                "virtual_keys": m.virtual_keys
            } for mid, m in self.machines.items()
        }

machine_manager = MachineManager()
