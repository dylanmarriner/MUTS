from typing import List

class DiagnosticsService:
    def read_dtcs(self) -> List[str]:
        # Simulated ECU response
        return ["P0101", "C0035"]

    def clear_dtcs(self) -> bool:
        # Always succeed in simulation
        return True
