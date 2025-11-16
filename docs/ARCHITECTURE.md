# Architecture

- GUI (PyQt)
  - Tabs: Dashboard, Diagnostics, Tuning, Security, Dyno.
  - Calls into services, does not touch hardware directly.

- Services
  - Business logic, queue building, safety policies.
  - No direct socket/CAN/J2534 — use a transport abstraction later.

- ECU Queue
  - Single FIFO for all write-type actions.
  - Supports simulation now; hardware executor later.

- Data
  - Future: logs, CSV exports, per-profile configs.

- Testing
  - pytest-based unit tests for services and queue behavior.
