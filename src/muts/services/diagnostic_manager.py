from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from ..storage import get_connection, ensure_demo_vehicle
from .mazda_obd import MazdaOBDService

DEFAULT_VIN = "7AT0C13JX20200064"


class DiagnosticManager:
    def __init__(self, vin: str = DEFAULT_VIN) -> None:
        ensure_demo_vehicle(vin)
        self._vin = vin
        self._obd = MazdaOBDService()

    def scan_dtcs(self) -> List[Dict[str, str]]:
        if not self._obd.connect():
            return []

        dtcs = self._obd.read_dtcs()
        now = datetime.utcnow().isoformat()
        with get_connection() as conn:
            for dtc in dtcs:
                code = dtc.get("code")
                if not code:
                    continue
                existing = conn.execute(
                    "SELECT id FROM trouble_codes WHERE vehicle_id = ? AND code = ? AND cleared_at IS NULL",
                    (self._vin, code),
                ).fetchone()
                if existing:
                    continue
                conn.execute(
                    "INSERT INTO trouble_codes (vehicle_id, code, description, severity, detected_at) VALUES (?, ?, ?, ?, ?)",
                    (
                        self._vin,
                        code,
                        dtc.get("description", ""),
                        dtc.get("severity", "MEDIUM"),
                        now,
                    ),
                )
            conn.commit()

        self._obd.disconnect()
        return self.list_dtcs()

    def clear_dtcs(self) -> bool:
        if not self._obd.connect():
            return False

        success = self._obd.clear_dtcs()
        if not success:
            self._obd.disconnect()
            return False

        now = datetime.utcnow().isoformat()
        with get_connection() as conn:
            conn.execute(
                "UPDATE trouble_codes SET cleared_at = ? WHERE vehicle_id = ? AND cleared_at IS NULL",
                (now, self._vin),
            )
            conn.commit()

        self._obd.disconnect()
        return True

    def list_dtcs(self) -> List[Dict[str, str]]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT code, description, severity, detected_at, cleared_at FROM trouble_codes WHERE vehicle_id = ?",
                (self._vin,),
            ).fetchall()
        result = []
        for row in rows:
            result.append(
                {
                    "code": row["code"],
                    "description": row["description"],
                    "severity": row["severity"],
                    "detected_at": row["detected_at"],
                    "cleared_at": row["cleared_at"],
                }
            )
        return result

    def record_live_data(self, payload: Dict[str, float]) -> Dict[str, float]:
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO ecu_data (
                    vehicle_id, timestamp, rpm, boost_psi, throttle_position,
                    ignition_timing, fuel_trim_long, fuel_trim_short, maf_voltage,
                    afr, coolant_temp, intake_temp, knock_count, vvt_advance,
                    calculated_load
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    self._vin,
                    datetime.utcnow().isoformat(),
                    payload.get("rpm"),
                    payload.get("boost_psi"),
                    payload.get("throttle_position"),
                    payload.get("ignition_timing"),
                    payload.get("fuel_trim_long"),
                    payload.get("fuel_trim_short"),
                    payload.get("maf_voltage"),
                    payload.get("afr"),
                    payload.get("coolant_temp"),
                    payload.get("intake_temp"),
                    payload.get("knock_count"),
                    payload.get("vvt_advance"),
                    payload.get("calculated_load"),
                ),
            )
            conn.commit()
        return payload

    def read_live_data(self) -> Dict[str, float]:
        if not self._obd.connect():
            return {}
        payload = self._obd.read_ecu_data()
        self._obd.disconnect()
        return payload

    def live_data(self) -> Dict[str, float]:
        payload = self.read_live_data()
        return self.record_live_data(payload)

    def health_report(self) -> Dict[str, object]:
        with get_connection() as conn:
            dtcs = conn.execute(
                "SELECT code FROM trouble_codes WHERE vehicle_id = ? AND cleared_at IS NULL",
                (self._vin,),
            ).fetchall()
            recent = conn.execute(
                "SELECT boost_psi, knock_count FROM ecu_data WHERE vehicle_id = ? ORDER BY timestamp DESC LIMIT 100",
                (self._vin,),
            ).fetchall()

        score = 100
        issues: List[str] = []

        if dtcs:
            score -= len(dtcs) * 10
            issues.extend([f"Active DTC: {row['code']}" for row in dtcs])

        if recent:
            avg_knock = sum(row["knock_count"] or 0 for row in recent) / len(recent)
            if avg_knock > 2:
                score -= 15
                issues.append("Elevated knock counts detected")
            avg_boost = sum(row["boost_psi"] or 0 for row in recent) / len(recent)
            if avg_boost > 18:
                score -= 10
                issues.append("High boost pressure detected")

        return {
            "health_score": max(score, 0),
            "issues": issues,
            "active_dtcs": [row["code"] for row in dtcs],
            "recommendations": [
                "Follow scheduled maintenance windows",
                "Monitor boost and temperature readings",
                "Inspect ignition if knock persists",
            ],
        }
