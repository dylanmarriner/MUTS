
# MUTS Build & Setup Instructions

## 1. Prerequisites

- OS: Windows 10/11, macOS, or modern Linux
- Python: 3.10+
- Git
- (Optional) Virtual environment tool: `venv`
- (Optional) CAN / J2534 hardware interface

## 2. Clone the Repository

```bash
git clone <YOUR_REPO_URL> muts
cd muts
```

## 3. Create Virtual Environment

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate
```

## 4. Install Dependencies

```bash
pip install -e ".[dev]"
```

This installs runtime + dev dependencies (pytest, ruff, mypy, black, etc.).

## 5. Run MUTS (GUI)

```bash
python -m muts
```

This should open the MUTS main window with tabs:
- Dashboard
- Diagnostics
- Tuning
- Security
- Dyno

## 6. Linting, Types, and Tests

```bash
# Lint
ruff check src

# Format
black src tests

# Type-check
mypy src

# Tests
pytest -q
```

Or simply:

```bash
make check
```

(if Make is available on your system).

## 7. Hardware Integration (High-Level)

1. Install drivers for your CAN or J2534 interface.
2. Configure OS-level interface (e.g. `can0` on Linux, J2534 DLL on Windows).
3. Implement or configure the MUTS transport layer to point to your device.
4. Start MUTS and select the appropriate interface in settings (to be implemented in the app).

## 8. Packaging (Optional)

For PyInstaller or similar tools, create a spec file that:
- Includes the `muts` package as the entry point
- Bundles Qt plugins and platform libraries
- Produces a single-folder or single-file executable

## 9. Recommended Workflow

1. Pull the latest changes from Git.
2. Create a feature branch.
3. Implement or modify features under `src/muts/`.
4. Run `make check` before committing.
5. Open a PR and link it to a task from `.ai/blueprints/tasks.yaml`.

