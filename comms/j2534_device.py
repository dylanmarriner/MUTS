"""Wrapper around a single J2534 DLL/device.

Provides a Pythonic interface for opening the device, making a CAN ISO15765
connection, and reading/writing raw PASSTHRU_MSG frames.
"""
from __future__ import annotations

import ctypes
import logging
from ctypes import c_ulong, c_long, POINTER, c_void_p, byref
from .j2534_api import PASSTHRU_MSG, STATUS_NOERROR, ISO15765

log = logging.getLogger(__name__)

class J2534Error(Exception):
    pass

class J2534Device:
    def __init__(self, dll_path: str, name: str = "Unknown J2534 device"):
        self.name = name
        self.dll_path = dll_path
        self.api = ctypes.WinDLL(dll_path)
        self.device_id = c_ulong(0)
        self.channel_id = c_ulong(0)
        self._define_prototypes()

    def _define_prototypes(self) -> None:
        self.api.PassThruOpen.argtypes = [c_void_p, POINTER(c_ulong)]
        self.api.PassThruOpen.restype = c_long

        self.api.PassThruClose.argtypes = [c_ulong]
        self.api.PassThruClose.restype = c_long

        self.api.PassThruConnect.argtypes = [
            c_ulong, c_ulong, c_ulong, c_ulong, POINTER(c_ulong)
        ]
        self.api.PassThruConnect.restype = c_long

        self.api.PassThruDisconnect.argtypes = [c_ulong]
        self.api.PassThruDisconnect.restype = c_long

        self.api.PassThruReadMsgs.argtypes = [
            c_ulong, POINTER(PASSTHRU_MSG), POINTER(c_ulong), c_ulong
        ]
        self.api.PassThruReadMsgs.restype = c_long

        self.api.PassThruWriteMsgs.argtypes = [
            c_ulong, POINTER(PASSTHRU_MSG), POINTER(c_ulong), c_ulong
        ]
        self.api.PassThruWriteMsgs.restype = c_long

    def open(self) -> None:
        result = self.api.PassThruOpen(None, byref(self.device_id))
        if result != STATUS_NOERROR:
            raise J2534Error(f"{self.name}: PassThruOpen failed ({result})")
        log.info("Opened J2534 device %s (id=%s)", self.name, self.device_id.value)

    def connect_iso15765(self, baud: int = 500000, flags: int = 0) -> None:
        result = self.api.PassThruConnect(
            self.device_id,
            ISO15765,
            flags,
            baud,
            byref(self.channel_id)
        )
        if result != STATUS_NOERROR:
            raise J2534Error(f"{self.name}: PassThruConnect failed ({result})")
        log.info("Connected ISO15765 channel %s", self.channel_id.value)

    def write_msg(self, data: bytes, tx_flags: int = 0, timeout_ms: int = 100) -> None:
        msg = PASSTHRU_MSG()
        msg.set_data(ISO15765, data, tx_flags=tx_flags)
        num_msgs = c_ulong(1)
        result = self.api.PassThruWriteMsgs(
            self.channel_id, byref(msg), byref(num_msgs), timeout_ms
        )
        if result != STATUS_NOERROR:
            raise J2534Error(f"PassThruWriteMsgs failed ({result})")

    def read_msgs(self, max_msgs: int = 10, timeout_ms: int = 100) -> list[PASSTHRU_MSG]:
        msgs = (PASSTHRU_MSG * max_msgs)()
        num_msgs = c_ulong(max_msgs)
        result = self.api.PassThruReadMsgs(
            self.channel_id, msgs, byref(num_msgs), timeout_ms
        )
        if result not in (STATUS_NOERROR,):
            # On timeout PassThru may return ERR_TIMEOUT; caller can ignore
            return []
        return [msgs[i] for i in range(num_msgs.value)]

    def close(self) -> None:
        if self.channel_id.value:
            try:
                self.api.PassThruDisconnect(self.channel_id)
            except Exception:
                log.exception("Error disconnecting J2534 channel")
            self.channel_id.value = 0
        if self.device_id.value:
            try:
                self.api.PassThruClose(self.device_id)
            except Exception:
                log.exception("Error closing J2534 device")
            self.device_id.value = 0
