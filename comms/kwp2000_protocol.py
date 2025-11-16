"""Minimal KWP2000 helper built on IsoTpTransport.

Some Mazda modules may still use KWP-style services for certain functions.
This implementation is intentionally minimal and can be expanded later.
"""
from __future__ import annotations

from .iso15765_transport import IsoTpTransport, IsoTpError

class KwpError(Exception):
    pass

class KwpClient:
    def __init__(self, transport: IsoTpTransport):
        self.tp = transport

    def _req(self, sid: int, data: bytes = b"") -> bytes:
        payload = bytes([sid]) + data
        resp = self.tp.request(payload)
        if not resp:
            raise KwpError("Empty KWP response")
        # KWP positive response = SID + 0x40
        if resp[0] != sid + 0x40:
            raise KwpError(f"Unexpected KWP response SID 0x{resp[0]:02X}")
        return resp[1:]

    def start_diagnostic_session(self, session: int = 0x85) -> None:
        self._req(0x10, bytes([session]))

    def read_data_by_local_id(self, lid: int) -> bytes:
        return self._req(0x21, bytes([lid]))

    def clear_dtc(self) -> None:
        self._req(0x14)
