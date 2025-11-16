"""UDS (ISO 14229) protocol helper on top of IsoTpTransport."""
from __future__ import annotations

import logging
from typing import Optional

from .iso15765_transport import IsoTpTransport, IsoTpError

log = logging.getLogger(__name__)

class UdsError(Exception):
    pass

class UdsClient:
    def __init__(self, transport: IsoTpTransport):
        self.tp = transport

    def _req(self, sid: int, data: bytes = b"", expect_positive: bool = True) -> bytes:
        payload = bytes([sid]) + data
        resp = self.tp.request(payload)
        if not resp:
            raise UdsError("Empty UDS response")
        resp_sid = resp[0]
        if resp_sid == 0x7F:  # negative response
            neg_sid = resp[1]
            code = resp[2]
            raise UdsError(f"Negative response to 0x{neg_sid:02X}: NRC=0x{code:02X}")
        if expect_positive and resp_sid != (sid + 0x40):
            raise UdsError(f"Unexpected UDS response SID 0x{resp_sid:02X} to 0x{sid:02X}")
        return resp[1:]

    def diag_session_control(self, session: int) -> None:
        self._req(0x10, bytes([session]))

    def ecu_reset(self, reset_type: int = 1) -> None:
        self._req(0x11, bytes([reset_type]))

    def read_data_by_id(self, did: int) -> bytes:
        did_bytes = did.to_bytes(2, "big")
        return self._req(0x22, did_bytes)

    def write_data_by_id(self, did: int, data: bytes) -> None:
        did_bytes = did.to_bytes(2, "big")
        self._req(0x2E, did_bytes + data)

    def security_access(self, level: int, seed: Optional[bytes] = None, key: Optional[bytes] = None) -> bytes:
        if seed is None:
            # request seed
            return self._req(0x27, bytes([level]))
        if key is None:
            raise UdsError("Key must be provided when sending security response")
        return self._req(0x27, bytes([level]) + key)

    def routine_control(self, control_type: int, routine_id: int, data: bytes = b"") -> bytes:
        rid = routine_id.to_bytes(2, "big")
        return self._req(0x31, bytes([control_type]) + rid + data)

    def request_download(self, addr: int, size: int) -> bytes:
        # Simplified: assume 32-bit address and size
        addr_bytes = addr.to_bytes(4, "big")
        size_bytes = size.to_bytes(4, "big")
        fmt = bytes([0x00, 0x44])  # dummy format
        return self._req(0x34, fmt + addr_bytes + size_bytes)

    def transfer_data(self, block_num: int, chunk: bytes) -> bytes:
        return self._req(0x36, bytes([block_num]) + chunk)

    def transfer_exit(self) -> None:
        self._req(0x37)

    def tester_present(self) -> None:
        try:
            self._req(0x3E, bytes([0x00]), expect_positive=True)
        except UdsError:
            log.debug("TesterPresent negative/ignored; continuing")
