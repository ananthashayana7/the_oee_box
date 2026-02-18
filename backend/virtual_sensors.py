class VirtualSensorFactory:
    def process(self, data, trust_scores):
        """
        Enhances data dict with virtual sensors based on heuristic rules.
        """
        virtual = data.copy()
        virtual_trust = trust_scores.copy()
        virtual_keys = []

        # Rule 1: Infer State from Amps/Power/Vibration if State Missing
        if "state_code" not in data or trust_scores.get("state_code", 0) < 0.5:
            # Look for proxy signals
            proxies = ["current_amps", "power", "vibration", "ch1_val"] # ch1 often generic analog
            proxy_key = next((k for k in proxies if k in data), None)

            if proxy_key:
                val = data[proxy_key]
                # Simple Threshold: If signal > 0.5 (noise floor), assume running
                new_state = 1 if abs(val) > 0.5 else 0
                virtual["state_code"] = new_state
                virtual_trust["state_code"] = trust_scores[proxy_key] * 0.9 # Slightly less trust than source
                virtual_keys.append("state_code (Virtual)")

        # Rule 2: Alias Production Count
        if "production_count" not in data:
            aliases = ["parts", "cycles", "count", "good_parts", "ch2_val"]
            alias_key = next((k for k in aliases if k in data), None)

            if alias_key:
                virtual["production_count"] = data[alias_key]
                virtual_trust["production_count"] = trust_scores[alias_key]
                virtual_keys.append("production_count (Alias)")

        return virtual, virtual_trust, virtual_keys

virtual_factory = VirtualSensorFactory()
