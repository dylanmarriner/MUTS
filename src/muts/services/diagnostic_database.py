from __future__ import annotations

from dataclasses import asdict
from typing import Dict, Iterable, List, Optional

import pids


class DiagnosticDatabaseService:
    def __init__(self) -> None:
        self.db = pids.Mazdaspeed3DiagnosticDatabase()

    def list_pids(
        self,
        query: str = "",
        mazda_only: Optional[bool] = None,
        proprietary_only: bool = False,
    ) -> List[Dict[str, str]]:
        query = query.strip().upper()
        entries = []
        for pid, definition in self.db.get_all_pids().items():
            is_mazda = definition.mazda_specific
            if mazda_only is True and not is_mazda:
                continue
            if mazda_only is False and is_mazda and proprietary_only is False:
                pass
            if proprietary_only and not pid.startswith("22"):
                continue
            if query and query not in pid and query not in definition.description.upper():
                continue
            entries.append(
                {
                    "pid": pid,
                    "description": definition.description,
                    "formula": definition.formula,
                    "units": definition.units,
                    "byte_length": str(definition.byte_length),
                    "mazda_specific": "yes" if is_mazda else "no",
                }
            )
        return entries

    def list_dtcs(
        self,
        severity: Optional[str] = None,
        mazda_specific: Optional[bool] = None,
        query: str = "",
    ) -> List[Dict[str, str]]:
        query = query.strip().upper()
        entries = []
        for code, definition in self.db.get_all_dtcs().items():
            if severity and definition.severity.upper() != severity.upper():
                continue
            if mazda_specific is not None and definition.mazda_specific != mazda_specific:
                continue
            if query and query not in code and query not in definition.description.upper():
                continue
            entries.append(
                {
                    "code": code,
                    "description": definition.description,
                    "severity": definition.severity,
                    "causes": "; ".join(definition.common_causes),
                    "steps": "; ".join(definition.diagnostic_steps),
                }
            )
        return entries

