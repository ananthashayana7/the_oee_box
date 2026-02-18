class SchemaInferenceEngine:
    def __init__(self):
        self.history = {} # key -> list of values
        self.schema = {} # key -> type
        self.max_history = 20

    def process(self, payload):
        """
        Ingests a dictionary payload (flattened if necessary).
        Updates internal history and re-evaluates schema.
        """
        for key, value in payload.items():
            if key not in self.history:
                self.history[key] = []

            self.history[key].append(value)
            if len(self.history[key]) > self.max_history:
                self.history[key].pop(0)

            self.infer_type(key)

    def infer_type(self, key):
        values = self.history[key]
        if not values:
            return

        # Check for Boolean
        if all(isinstance(v, bool) for v in values):
            self.schema[key] = "Boolean"
            return

        # Check for Numeric
        if all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in values):
            # Special case: Timestamp
            if "timestamp" in key.lower() or "time" in key.lower():
                self.schema[key] = "Timestamp"
                return

            unique_values = set(values)

            # Check for Constant value (Ambiguous, but likely not an active Counter)
            if len(unique_values) == 1:
                val = list(unique_values)[0]
                if float(val).is_integer() and val <= 5:
                    self.schema[key] = "State"
                else:
                    self.schema[key] = "Gauge"
                return

            # Check for Counter (Monotonically Increasing)
            # Allow for equal values (e.g. machine stopped), so <=
            is_monotonic = all(values[i] <= values[i+1] for i in range(len(values)-1))

            if is_monotonic:
                self.schema[key] = "Counter"
                return

            # Check for State (Discrete, few unique values, integers)
            if len(unique_values) <= 5 and all(float(v).is_integer() for v in unique_values):
                 self.schema[key] = "State"
                 return

            # Default to Gauge (fluctuating)
            self.schema[key] = "Gauge"
            return

        self.schema[key] = "Text"

    def get_schema(self):
        return self.schema
