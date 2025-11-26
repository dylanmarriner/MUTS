from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

DB_PATH = Path(".muts_data.sqlite")

SCHEMA = """
CREATE TABLE IF NOT EXISTS vehicles (
    id TEXT PRIMARY KEY,
    model TEXT NOT NULL,
    ecu_type TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ecu_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    rpm INTEGER,
    boost_psi REAL,
    throttle_position REAL,
    ignition_timing REAL,
    fuel_trim_long REAL,
    fuel_trim_short REAL,
    maf_voltage REAL,
    afr REAL,
    coolant_temp REAL,
    intake_temp REAL,
    knock_count INTEGER,
    vvt_advance REAL,
    calculated_load REAL,
    FOREIGN KEY(vehicle_id) REFERENCES vehicles(id)
);

CREATE TABLE IF NOT EXISTS trouble_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id TEXT NOT NULL,
    code TEXT NOT NULL,
    description TEXT,
    severity TEXT,
    detected_at TEXT NOT NULL,
    cleared_at TEXT,
    FOREIGN KEY(vehicle_id) REFERENCES vehicles(id)
);
"""


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(SCHEMA)


@contextmanager
def get_connection(path: Path | str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def ensure_demo_vehicle(vin: str = "7AT0C13JX20200064") -> None:
    init_db()
    with get_connection() as conn:
        cursor = conn.execute("SELECT id FROM vehicles WHERE id = ?", (vin,))
        if cursor.fetchone():
            return
        conn.execute(
            "INSERT INTO vehicles (id, model, ecu_type, created_at) VALUES (?, ?, ?, ?)",
            (vin, "Mazdaspeed 3 2011", "MZR 2.3L DISI TURBO", datetime.utcnow().isoformat()),
        )
        conn.commit()
