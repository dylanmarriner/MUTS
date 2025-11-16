"""ISO-TP (ISO 15765-2) transport over J2534.

This is a minimal implementation sufficient for typical request/response
UDS traffic. It is not optimized for very high throughput.
"""
from __future__ import annotations

import logging
from typing import Optional

from .j2534_api import PASSTHRU_MSG, ISO15765
from .j2534_device import J2534Device

log = logging.getLogger(__name__)

PCI_SINGLE = 0x0
PCI_FIRST  = 0x1
PCI_CONSEC = 0x2
PCI_FLOW   = 0x3

class IsoTpError(Exception):
    pass

class IsoTpTransport:
    def __init__(self, dev: J2534Device, tx_id: int, rx_id: int):
        self.dev = dev
        self.tx_id = tx_id
        self.rx_id = rx_id

    def _build_can_frame(self, can_id: int, payload: bytes) -> bytes:
        # For J2534 ISO15765, we embed CAN ID in the first 4 bytes of Data
        # Format: 4-byte ID + up to 8 bytes payload.
        # Here we use 11-bit ID in the lower bits.
        data = bytearray(4 + len(payload))
        data[0] = (can_id >> 24) & 0xFF
        data[1] = (can_id >> 16) & 0xFF
        data[2] = (can_id >> 8) & 0xFF
        data[3] = can_id & 0xFF
        data[4:] = payload
        return bytes(data)

    def _parse_can_frame(self, msg: PASSTHRU_MSG) -> tuple[int, bytes]:
        raw = bytes(msg.Data[: msg.DataSize])
        if len(raw) < 5:
            raise IsoTpError("Short frame from J2534")
        can_id = (raw[0] << 24) | (raw[1] << 16) | (raw[2] << 8) | raw[3]
        payload = raw[4:]
        return can_id, payload

    def request(self, payload: bytes, timeout_ms: int = 500) -> bytes:
        """Send a single ISO-TP request and return the reassembled response."""
        # Very basic: assume responses fit in a single/multi-frame dialog.
        # Build first frame logic if needed.
        if len(payload) <= 7:
            # Single frame
            length = len(payload)
            sf_pci = (PCI_SINGLE << 4) | length
            frame_payload = bytes([sf_pci]) + payload
            frame = self._build_can_frame(self.tx_id, frame_payload)
            self.dev.write_msg(frame)
        else:
            # Multi-frame transmit (first frame + consecutive)
            total_len = len(payload)
            ff_pci = (PCI_FIRST << 4) | ((total_len >> 8) & 0x0F)
            ff_len_low = total_len & 0xFF
            frame_payload = bytes([ff_pci, ff_len_low]) + payload[:6]
            frame = self._build_can_frame(self.tx_id, frame_payload)
            self.dev.write_msg(frame)

            # In a full implementation we would wait for flow control (FC) here;
            # for simplicity we assume the ECU is permissive.

            idx = 6
            seq = 1
            while idx < total_len:
                chunk = payload[idx : idx + 7]
                cf_pci = (PCI_CONSEC << 4) | (seq & 0x0F)
                frame_payload = bytes([cf_pci]) + chunk
                frame = self._build_can_frame(self.tx_id, frame_payload)
                self.dev.write_msg(frame)
                idx += len(chunk)
                seq = (seq + 1) & 0x0F

        # Read response frames and reassemble
        data = bytearray()
        expected_len: Optional[int] = None
        while True:
            msgs = self.dev.read_msgs(max_msgs=10, timeout_ms=timeout_ms)
            if not msgs:
                raise IsoTpError("No response from ECU")
            for m in msgs:
                can_id, pl = self._parse_can_frame(m)
                if can_id != self.rx_id or not pl:
                    continue
                pci_type = (pl[0] >> 4) & 0x0F
                if pci_type == PCI_SINGLE:
                    length = pl[0] & 0x0F
                    data.extend(pl[1 : 1 + length])
                    return bytes(data)
                elif pci_type == PCI_FIRST:
                    high = pl[0] & 0x0F
                    low = pl[1]
                    expected_len = (high << 8) | low
                    data.extend(pl[2:])
                    if len(data) >= expected_len:
                        return bytes(data[:expected_len])
                elif pci_type == PCI_CONSEC:
                    data.extend(pl[1:])
                    if expected_len is not None and len(data) >= expected_len:
                        return bytes(data[:expected_len])
