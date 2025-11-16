"""High level Mazda ECU interface for MUTS.

This class hides the details of J2534, ISO-TP, and UDS/KWP and exposes
domain-specific methods for diagnostics, live data, map access, and flashing.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Dict, Optional

from .j2534_manager import J2534Manager
from .iso15765_transport import IsoTpTransport
from .uds_protocol import UdsClient, UdsError

log = logging.getLogger(__name__)

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

class MazdaEcu:
    """ECU interface focused on the 2011 Mazdaspeed 3 platform."""

    def __init__(self, config_path: str = "config/j2534_devices.yml"):
        self.jm = J2534Manager(config_path)
        self.device = None
        self.transport: Optional[IsoTpTransport] = None
        self.uds: Optional[UdsClient] = None
        # Typical Mazda ECM CAN IDs; may be overridden by config in future
        self.tx_id = 0x7E0
        self.rx_id = 0x7E8

    def connect(self) -> None:
        dev = self.jm.auto_connect_first()
        if not dev:
            raise RuntimeError("No J2534 device available/connected")
        self.device = dev
        self.transport = IsoTpTransport(dev, self.tx_id, self.rx_id)
        self.uds = UdsClient(self.transport)
        # Enter extended diagnostic session if needed
        try:
            self.uds.diag_session_control(0x03)
        except UdsError:
            log.warning("Extended diag session not accepted; continuing")

    def disconnect(self) -> None:
        if self.device:
            self.device.close()
        self.device = None
        self.transport = None
        self.uds = None

    # --- Live data & diagnostics ---

    def read_live_data(self) -> LiveData:
        """Read a core set of live data items via UDS DIDs.

        NOTE: The exact DIDs are ECU-specific and may need adjustment.
        Here we assume Mazda-specific IDs for demonstration.
        """
        if not self.uds:
            raise RuntimeError("ECU not connected")

        def did_u16(did: int) -> int:
            data = self.uds.read_data_by_id(did)
            return int.from_bytes(data, "big")

        # These DIDs are placeholders and should be updated for real hardware
        rpm = did_u16(0x0C)            # engine speed
        throttle = did_u16(0x11) / 10  # %
        load = did_u16(0x04) / 100     # relative load
        boost_kpa = did_u16(0x70)      # example
        boost_psi = boost_kpa * 0.145038
        afr_cmd = 14.7                 # placeholder
        afr_act = 14.7                 # placeholder
        fuel_pressure_psi = did_u16(0x5A) * 0.145038
        ign = did_u16(0x0E) / 10
        knock = 0.0                    # placeholder
        iat_c = did_u16(0x0F) - 40
        ect_c = did_u16(0x05) - 40
        vss = did_u16(0x0D)

        return LiveData(
            rpm=rpm,
            throttle=throttle,
            engine_load=load,
            boost_psi=boost_psi,
            afr_commanded=afr_cmd,
            afr_actual=afr_act,
            fuel_pressure_psi=fuel_pressure_psi,
            ignition_advance_deg=ign,
            knock_retard_deg=knock,
            iat_c=iat_c,
            ect_c=ect_c,
            vehicle_speed_kph=vss,
        )

    def read_dtc_ecm(self) -> List[str]:
        """Read ECM DTCs via a UDS routine or manufacturer-specific DID.

        For now this returns an empty list and is intended to be implemented
        with real Mazda DTC services once reverse-engineered.
        """
        # Placeholder implementation
        return []

    # --- Flashing support ---

    def flash_rom(self, rom_image: bytes, start_addr: int, block_size: int = 0x400) -> None:
        """Flash a full ROM image to the ECU.

        This is a *dangerous* operation and should only be called after
        safety checks, checksum validation, and a stable power supply are
        confirmed by higher-level logic.
        """
        if not self.uds:
            raise RuntimeError("ECU not connected")

        total_size = len(rom_image)
        log.info("Starting flash: %d bytes from 0x%08X", total_size, start_addr)

        # Enter programming session and perform security access if required.
        try:
            self.uds.diag_session_control(0x02)  # programming session
        except Exception:
            log.exception("Failed to enter programming session")
            raise

        # In a real implementation we would:
        # 1) RequestDownload
        # 2) TransferData with sequential block numbers
        # 3) TransferExit
        # The details depend heavily on Mazda's bootloader.

        # Simple chunked transfer stub:
        block_num = 1
        offset = 0
        self.uds.request_download(start_addr, total_size)

        while offset < total_size:
            chunk = rom_image[offset : offset + block_size]
            self.uds.transfer_data(block_num, chunk)
            offset += len(chunk)
            block_num += 1
            log.debug("Flashed %d/%d bytes", offset, total_size)

        self.uds.transfer_exit()
        log.info("Flash complete, requesting ECU reset")
        self.uds.ecu_reset(0x01)
