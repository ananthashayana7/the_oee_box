import unittest
import sys
import os

# Add parent directory to path so we can import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.schema_inference import SchemaInferenceEngine

class TestSchemaInference(unittest.TestCase):
    def test_counter(self):
        engine = SchemaInferenceEngine()
        data = [
            {"count": 10},
            {"count": 11},
            {"count": 12},
            {"count": 12}, # Machine stopped
            {"count": 13}
        ]
        for d in data:
            engine.process(d)

        self.assertEqual(engine.schema["count"], "Counter")

    def test_gauge(self):
        engine = SchemaInferenceEngine()
        data = [
            {"temp": 40.1},
            {"temp": 40.5},
            {"temp": 39.8},
            {"temp": 40.2}
        ]
        for d in data:
            engine.process(d)

        self.assertEqual(engine.schema["temp"], "Gauge")

    def test_state(self):
        engine = SchemaInferenceEngine()
        data = [
            {"state": 1},
            {"state": 1},
            {"state": 0},
            {"state": 2},
            {"state": 1}
        ]
        for d in data:
            engine.process(d)

        self.assertEqual(engine.schema["state"], "State")

    def test_timestamp(self):
        engine = SchemaInferenceEngine()
        data = [
            {"timestamp": 1000},
            {"timestamp": 1001},
            {"timestamp": 1002}
        ]
        for d in data:
            engine.process(d)

        self.assertEqual(engine.schema["timestamp"], "Timestamp")

    def test_constant_state(self):
        engine = SchemaInferenceEngine()
        data = [{"state": 1}, {"state": 1}]
        for d in data: engine.process(d)
        self.assertEqual(engine.schema["state"], "State")

    def test_constant_gauge(self):
        engine = SchemaInferenceEngine()
        data = [{"temp": 20}, {"temp": 20}]
        for d in data: engine.process(d)
        self.assertEqual(engine.schema["temp"], "Gauge")

if __name__ == '__main__':
    unittest.main()
