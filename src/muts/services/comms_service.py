from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Mapping, Sequence


@dataclass
class CommunicationProtocol:
    name: str
    transport: str
    description: str
    request_example: str
    tx_id: str
    rx_id: str


@dataclass
class J2534DeviceInfo:
    name: str
    protocol: str
    dll: str
    connected: bool


class CommunicationService:
    PROTOCOLS: Sequence[CommunicationProtocol] = (
        CommunicationProtocol(
            name="ISO 15765-4 (CAN)",
            transport="ISO-TP over CAN",
            description="Standard Mazda diagnostic transport for UDS/ISO-TP traffic on 11-bit IDs.",
            request_example="10 02 (Session Control)",
            tx_id="0x7E0",
            rx_id="0x7E8",
        ),
        CommunicationProtocol(
            name="UDS (ISO 14229)",
            transport="ISO-TP + Service IDs",
            description="ECU configuration/diagnostic services built on ISO-TP (0x10,0x22,0x2E...).",
            request_example="22 F1 90 (Read VIN)",
            tx_id="0x7E0",
            rx_id="0x7E8",
        ),
        CommunicationProtocol(
            name="KWP2000 (Legacy)",
            transport="KWP-over-ISO-TP",
            description="Mazda still exposes some services via KWP2000 for legacy modules.",
            request_example="21 01 (Read local ID 0x01)",
            tx_id="0x7DF",
            rx_id="0x7E8",
        ),
    )

    DEVICES: List[J2534DeviceInfo] = [
        J2534DeviceInfo(
            name="SimAccessPort",
            protocol="ISO15765",
            dll="simap.dll",
            connected=False,
        ),
        J2534DeviceInfo(
            name="CobbLegacy", protocol="ISO15765", dll="cobb.dll", connected=False
        ),
    ]

    def __init__(self) -> None:
        self._devices = {dev.name: dev for dev in self.DEVICES}

    def list_protocols(self) -> Sequence[CommunicationProtocol]:
        return self.PROTOCOLS

    def simulate_transaction(self, protocol_name: str) -> str:
        payload = random.randint(0, 0xFFFF)
        return f"{protocol_name} response: {payload:04X}"

    def list_devices(self) -> List[J2534DeviceInfo]:
        return list(self._devices.values())

    def toggle_device(self, name: str) -> bool:
        device = self._devices.get(name)
        if not device:
            return False
        device.connected = not device.connected
        return device.connected
