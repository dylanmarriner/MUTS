"""Low-level J2534 API definitions using ctypes.

This module defines the PASSTHRU_MSG struct and constants required to call
vendor-supplied J2534 DLLs. It does not contain any Mazda-specific logic.
"""
from __future__ import annotations

import ctypes
from ctypes import c_ulong, c_long, c_ubyte, c_ushort, c_uint, c_void_p

# J2534 return codes (partial; extend as needed)
STATUS_NOERROR = 0
ERR_TIMEOUT = 12

# Protocol IDs
ISO15765 = 6

# Message flags
TX_MSG_TYPE = 0x00000000
RX_MSG_TYPE = 0x00000001

class PASSTHRU_MSG(ctypes.Structure):
    _fields_ = [
        ("ProtocolID", c_ulong),
        ("RxStatus", c_ulong),
        ("TxFlags", c_ulong),
        ("Timestamp", c_ulong),
        ("DataSize", c_ulong),
        ("ExtraDataIndex", c_ulong),
        ("Data", c_ubyte * 4128),
    ]

    def set_data(self, protocol_id: int, data: bytes, tx_flags: int = 0) -> None:
        self.ProtocolID = protocol_id
        self.RxStatus = 0
        self.TxFlags = tx_flags
        self.Timestamp = 0
        self.DataSize = len(data)
        self.ExtraDataIndex = 0
        for i, b in enumerate(data):
            self.Data[i] = b
