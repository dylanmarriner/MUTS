
# MUTS High-Level Architecture

MUTS is split into clear layers:

- GUI Layer (PyQt): Tabs for Dashboard, Diagnostics, Tuning, Security, Dyno.
- Service Layer: Business logic, ECU queue handling, safety rules.
- Transport Layer: Simulation now, J2534 / CAN later.
- Data Layer: Logging, future SQLite storage, exports.
- Integration: AI tuning, Limit Finder, etc. in future versions.
