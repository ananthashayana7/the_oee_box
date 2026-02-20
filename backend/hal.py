from backend.drivers.modbus_driver import ModbusDriver
from backend.drivers.opcua_driver import OPCUADriver

class HAL:
    @staticmethod
    def create_driver(protocol, config):
        if protocol == "modbus":
            return ModbusDriver(config)
        elif protocol == "opcua":
            return OPCUADriver(config)
        else:
            raise ValueError(f"Unknown protocol: {protocol}")

    def normalize(self, raw_data):
        # Flatten proprietary nesting or map keys
        return raw_data
