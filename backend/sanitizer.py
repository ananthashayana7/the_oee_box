import logging
import math
from collections import deque

logger = logging.getLogger("sanitizer")

class DataSanitizer:
    def __init__(self):
        self.rolling_windows = {} # key -> deque(maxlen=20)
        self.trust_scores = {} # key -> float (0.0 to 1.0)
        self.explanations = {} # key -> str
        self.min_trust = 0.5
        self.max_history = 20

    def process(self, data):
        """
        Takes raw data dict.
        Returns (sanitized_data, trust_scores).
        """
        sanitized = {}
        trust_scores = {}

        # 1. Check for expected keys? No, auto-discovery.
        # 2. For numeric fields, check for physics constraints (spikes)

        for key, value in data.items():
            if key == "timestamp":
                sanitized[key] = value
                trust_scores[key] = 1.0
                continue

            # Non-numeric? Pass through but trust=0.5 (unknown quality) unless mapped
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                sanitized[key] = value
                trust_scores[key] = 0.5
                continue

            # Numeric Sanitization
            if key not in self.rolling_windows:
                self.rolling_windows[key] = deque(maxlen=self.max_history)
                self.trust_scores[key] = 1.0 # Optimistic start

            window = self.rolling_windows[key]
            current_trust = self.trust_scores[key]

            # Physics Check: Z-Score / Variance
            if len(window) > 5:
                avg = sum(window) / len(window)
                variance = sum((x - avg) ** 2 for x in window) / len(window)
                std_dev = math.sqrt(variance)

                # Dynamic Threshold: If variance is low, even small changes trigger spikes?
                # Or just use % change from average.
                # Let's use simpler logic for robustness:
                # If value > 2x average (and average > 1), it's suspicious.
                # Or if value jumps significantly from last value.

                last_val = window[-1]
                # Avoid division by zero
                if abs(last_val) > 0.01:
                    percent_change = abs(value - last_val) / abs(last_val)

                    if percent_change > 0.5: # 50% jump in one step
                        # Spike Detected!
                        # Hold last value (Coasting Mode)
                        sanitized_val = last_val
                        trust_scores[key] = max(0.1, current_trust - 0.2)
                        self.explanations[key] = f"Spike detected: {last_val} -> {value}"
                        logger.warning(f"Sanitizer: Spike in {key} ({last_val} -> {value}). Coasting.")
                    else:
                        sanitized_val = value
                        trust_scores[key] = min(1.0, current_trust + 0.1) # Slowly regain trust
                        self.explanations[key] = "Signal stable"
                else:
                    sanitized_val = value
                    trust_scores[key] = 1.0
                    self.explanations[key] = "Baseline established"
            else:
                sanitized_val = value
                trust_scores[key] = 1.0
                self.explanations[key] = "Initializing history"

            sanitized[key] = sanitized_val
            window.append(sanitized_val) # Append the *sanitized* value to history to smooth further
            self.trust_scores[key] = trust_scores[key]

        return sanitized, trust_scores, self.explanations

sanitizer = DataSanitizer()
