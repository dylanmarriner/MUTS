from typing import Dict, List

from .diagnostic_manager import DiagnosticManager

class DiagnosticsService:
    def __init__(self, vin: str = "7AT0C13JX20200064") -> None:
        self.manager = DiagnosticManager(vin)

    def read_dtcs(self) -> List[Dict[str, str]]:
        return self.manager.scan_dtcs()

    def clear_dtcs(self) -> bool:
        return self.manager.clear_dtcs()
