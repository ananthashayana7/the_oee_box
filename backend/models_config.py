from pydantic import BaseModel

class MachineConfig(BaseModel):
    machine_id: str | None = None
    ideal_cycle_time: float # seconds
    shift_start_hour: int # 0-23
    target_availability: float = 0.90
    target_performance: float = 0.95
    target_quality: float = 0.99
