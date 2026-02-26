import struct
import logging
import time

logger = logging.getLogger("binary_parser")

class BinaryParser:
    def __init__(self):
        # Define C-Struct Format
        # Alignment: C structs often have padding. Assuming 'packed' for efficiency or standard alignment.
        # Let's assume standard little-endian (<).

        # Structure Definition:
        # 1. baseTimestamp: uint32 (4 bytes)
        # 2. macaddr: 15 chars (15 bytes) -> Maybe padded to 16? Let's assume 15 for now.
        # 3. uid: 15 chars (15 bytes) -> "macaddr & uid" might be one field? User said "macaddr & uid: 15 character unique hardware id". Let's assume 15 bytes total.

        # Power Measurement:
        # currentRMS[3][30]: 3 phases, 30 samples. Float? "RMS" usually float. 3 * 30 * 4 = 360 bytes.
        # voltageRMS[3][30]: 3 phases, 30 samples. Float. 360 bytes.

        # Environment:
        # temp, humidity, battery: 30 samples? Or 1 sample per 30 sec?
        # "sampled fir every 30 sec" -> likely 1 sample each. 3 * 4 = 12 bytes.

        # Analog/Digital:
        # analogInputs[9][30]: 12 bit precision... usually stored as uint16 (2 bytes). 9 * 30 * 2 = 540 bytes.
        # Digital[10][30]: uint16 (pulse count). 10 * 30 * 2 = 600 bytes.
        # Special Digital: 0/1. "sampled fir every 30 sec"? Let's assume 1 byte or uint32 bitmap. Let's guess 1 byte for now.

        # Barcode: 32 bytes.

        # Total Size Estimate:
        # 4 + 15 + 360 + 360 + 12 + 540 + 600 + 1 + 32 = ~1924 bytes.

        pass

    def parse(self, payload: bytes) -> list[dict]:
        """
        Parses the binary payload into a list of 30 JSON records (one per second).
        """
        try:
            offset = 0

            # 1. Base Timestamp (uint32)
            base_timestamp = struct.unpack_from('<I', payload, offset)[0]
            offset += 4

            # 2. UID (15s)
            uid_bytes = struct.unpack_from('<15s', payload, offset)[0]
            uid = uid_bytes.decode('utf-8').strip('\x00')
            offset += 15

            # Alignment padding? C structs often pad to 4 bytes.
            # 15 is odd. There might be 1 byte padding. Let's attempt strict packing first.

            # 3. Power (Current RMS) [3][30] floats
            # Layout: Phase 1 (30), Phase 2 (30), Phase 3 (30) OR Sample 1 (P1,P2,P3)...?
            # Standard C multidimensional array `float current[3][30]` is contiguous.
            # Row-major: Phase 0 (all 30 samples), Phase 1 (all 30)...
            current_rms = []
            for _ in range(3): # 3 Phases
                phase_data = struct.unpack_from('<30f', payload, offset)
                current_rms.append(phase_data)
                offset += 30 * 4

            # 4. Power (Voltage RMS) [3][30] floats
            voltage_rms = []
            for _ in range(3):
                phase_data = struct.unpack_from('<30f', payload, offset)
                voltage_rms.append(phase_data)
                offset += 30 * 4

            # 5. Environment (Single sample for 30s window)
            temp, humidity, battery = struct.unpack_from('<3f', payload, offset)
            offset += 3 * 4

            # 6. Analog Inputs [9][30] uint16
            analog = []
            for _ in range(9):
                ch_data = struct.unpack_from('<30H', payload, offset)
                analog.append(ch_data)
                offset += 30 * 2

            # 7. Digital Inputs [10][30] uint16
            digital = []
            for _ in range(10):
                ch_data = struct.unpack_from('<30H', payload, offset)
                digital.append(ch_data)
                offset += 30 * 2

            # 8. Special Digital (uint8?)
            special = struct.unpack_from('<B', payload, offset)[0]
            offset += 1

            # 9. Barcode (32s)
            barcode_bytes = struct.unpack_from('<32s', payload, offset)[0]
            barcode = barcode_bytes.decode('utf-8').strip('\x00')
            offset += 32

            # Generate 30 records
            records = []
            for i in range(30):
                record = {
                    "machine_id": uid,
                    "timestamp": base_timestamp + i, # Second-by-second resolution
                    "temperature": temp,
                    "humidity": humidity,
                    "battery": battery,
                    "special_input": special,
                    "barcode": barcode,
                    # Derived Metrics
                    "state_code": 1 if current_rms[0][i] > 0.1 else 0, # Heuristic: Current > 0.1 = Running
                }

                # Add arrays flattened
                for ph in range(3):
                    record[f"current_p{ph+1}"] = current_rms[ph][i]
                    record[f"voltage_p{ph+1}"] = voltage_rms[ph][i]

                for ch in range(9):
                    record[f"analog_{ch+1}"] = analog[ch][i]

                for ch in range(10):
                    record[f"digital_{ch+1}"] = digital[ch][i]

                records.append(record)

            return records

        except Exception as e:
            logger.error(f"Binary Parse Error: {e}")
            return []

binary_parser = BinaryParser()
