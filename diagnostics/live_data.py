"""Live data polling based on MazdaEcu.read_live_data()."""
from __future__ import annotations

import time
import threading
from typing import Callable, Optional
from dataclasses import dataclass

from comms.mazda_ecu import MazdaEcu, LiveData

@dataclass
class LiveDataSample:
    timestamp: float
    data: LiveData

class LiveDataPoller:
    def __init__(self, ecu: MazdaEcu, interval: float = 0.2):
        self.ecu = ecu
        self.interval = interval
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self.callback: Optional[Callable[[LiveDataSample], None]] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while not self._stop.is_set():
            ts = time.time()
            try:
                data = self.ecu.read_live_data()
                sample = LiveDataSample(timestamp=ts, data=data)
                if self.callback:
                    self.callback(sample)
            except Exception:
                # In production we would log this
                pass
            time.sleep(self.interval)

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1.0)
