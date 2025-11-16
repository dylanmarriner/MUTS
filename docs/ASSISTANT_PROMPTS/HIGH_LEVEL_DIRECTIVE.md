You are implementing MUTS (Mazda Ultimate Technician Suite).

Follow the specs in the docs directory. Never write directly to hardware from GUI code.
All write-type operations must go through the ECU queue and then a transport abstraction
(simulation now, J2534 later).

Target:
- Python 3.10+
- PyQt5 for GUI
- pytest for tests
- Ruff + Black for style
