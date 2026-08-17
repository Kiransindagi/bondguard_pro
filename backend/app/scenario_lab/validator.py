import math
from typing import Any


class ScenarioValidator:
    @staticmethod
    def validate_shocks(shocks: dict[str, Any]):
        """
        Enforce validation bounds and sanity checks on scenario shock inputs.
        """
        for key, val in shocks.items():
            if val is None:
                continue
            
            # Check for numeric type
            if not isinstance(val, (int, float)):
                try:
                    val = float(val)
                except (ValueError, TypeError):
                    raise ValueError(f"Shock for {key} must be a numeric value.")

            # Check for NaN and Infinity
            if math.isnan(val) or math.isinf(val):
                raise ValueError(f"Shock for {key} cannot be NaN or Infinity.")

            # Check reasonable bounds (e.g., -1000 bps to +1000 bps)
            if val < -1000 or val > 1000:
                raise ValueError(f"Shock for {key} ({val} bps) exceeds validation bounds of [-1000, 1000] bps.")
