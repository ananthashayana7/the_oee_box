from backend.schema_inference import SchemaInferenceEngine
from backend.oee import OEECalculator
from backend.sanitizer import DataSanitizer
from backend.virtual_sensors import VirtualSensorFactory
import logging
import asyncio
from backend.database import db_manager

logger = logging.getLogger("machine_manager")

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
            # Try to load config in background
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._load_config(machine_id))
            except RuntimeError:
                pass # Running in test/script context maybe?
        return self.machines[machine_id]

    async def _load_config(self, machine_id):
        try:
            config = await db_manager.get_machine_config(machine_id)
            if config:
                if machine_id in self.machines:
                    self.machines[machine_id].oee_calculator.set_config(config)
                    logger.info(f"Loaded config for {machine_id}: {config}")
        except Exception as e:
            logger.warning(f"Failed to load config for {machine_id}: {e}")

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
