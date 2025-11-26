"""Live data reading service."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from comms.uds_protocol import UdsClient


@dataclass
class LiveData:
    rpm: int
    throttle: float
    engine_load: float
    boost_psi: float
    afr_commanded: float
    afr_actual: float
    fuel_pressure_psi: float
    ignition_advance_deg: float
    knock_retard_deg: float
    iat_c: float
    ect_c: float
    vehicle_speed_kph: float


class LiveDataService:
    def __init__(self, uds_client: UdsClient):
        self.uds = uds_client

    def _read_did_u16(self, did: int) -> int:
        data = self.uds.read_data_by_id(did)
        return int.from_bytes(data, "big")

    def read_rpm(self) -> int:
        return self._read_did_u16(0x0C)

    def read_throttle(self) -> float:
        return self._read_did_u16(0x11) / 10

    def read_engine_load(self) -> float:
        return self._read_did_u16(0x04) / 100

    def read_boost_psi(self) -> float:
        boost_kpa = self._read_did_u16(0x70)
        return boost_kpa * 0.145038

    def read_fuel_pressure_psi(self) -> float:
        return self._read_did_u16(0x5A) * 0.145038

    def read_ignition_advance(self) -> float:
        return self._read_did_u16(0x0E) / 10

    def read_iat(self) -> float:
        return self._read_did_u16(0x0F) - 40

    def read_ect(self) -> float:
        return self._read_did_u16(0x05) - 40

    def read_vehicle_speed(self) -> int:
        return self._read_did_u16(0x0D)

    def read_all_live_data(self) -> LiveData:
        # Placeholder values for data not read from DIDs
        afr_cmd = 14.7
        afr_act = 14.7
        knock = 0.0

        return LiveData(
            rpm=self.read_rpm(),
            throttle=self.read_throttle(),
            engine_load=self.read_engine_load(),
            boost_psi=self.read_boost_psi(),
            afr_commanded=afr_cmd,
            afr_actual=afr_act,
            fuel_pressure_psi=self.read_fuel_pressure_psi(),
            ignition_advance_deg=self.read_ignition_advance(),
            knock_retard_deg=knock,
            iat_c=self.read_iat(),
            ect_c=self.read_ect(),
            vehicle_speed_kph=self.read_vehicle_speed(),
        )
