# MUTS Desktop - Mazda Universal Tuning System

A desktop ECU tuning application built with Electron, Node.js, and Rust for safety-critical operations.

## Architecture

- **Rust Core**: Hardware interface abstraction, streaming telemetry, diagnostics, flash operations, and safety system
- **Node Backend**: IPC handlers, session management, database operations, and business logic
- **Electron UI**: React-based interface with 10 functional tabs

## Features

- Real-time telemetry streaming with CAN signal decoding
- Diagnostic request handling with DTC management
- ROM validation, checksum verification, and flashing
- Safety-first workflows with explicit arming levels
- AI tuner integration for optimization recommendations
- Comprehensive logging and timeline tracking

## Prerequisites

- Node.js 18+ 
- Rust 1.70+
- PostgreSQL (for database features)

## Installation

1. Clone and navigate to the project:
```bash
cd muts-desktop
```

2. Run the installation script:
```bash
chmod +x install.sh
./install.sh
```

Or install manually:

```bash
# Install Node backend dependencies
cd node-backend
npm install

# Install Electron UI dependencies
cd ../electron-ui
npm install

# Build Rust core
cd ../rust-core
cargo build --release
```

## Running the Application

1. Start the Node backend:
```bash
cd node-backend
npm run dev
```

2. In a new terminal, start the Electron UI:
```bash
cd electron-ui
npm run dev
```

## Project Structure

```
muts-desktop/
├── rust-core/          # Rust safety-critical core
│   ├── src/
│   │   ├── lib.rs      # Main library with N-API exports
│   │   ├── hardware.rs # Hardware abstraction
│   │   ├── streaming.rs # Telemetry streaming
│   │   ├── diagnostics.rs # Diagnostic protocols
│   │   ├── flash.rs    # Flash operations
│   │   ├── safety.rs   # Safety system
│   │   └── types.rs    # Shared types
│   └── Cargo.toml
├── node-backend/       # Node.js backend
│   ├── src/
│   │   ├── index.ts    # Main entry point
│   │   ├── core/       # Core modules
│   │   │   ├── rust-core.ts
│   │   │   ├── session-manager.ts
│   │   │   ├── database-manager.ts
│   │   │   └── safety-manager.ts
│   │   ├── ipc/        # IPC handlers
│   │   │   └── handlers.ts
│   │   └── utils/
│   │       └── logger.ts
│   ├── package.json
│   └── tsconfig.json
└── electron-ui/        # Electron UI
    ├── src/
    │   ├── main.ts     # Electron main process
    │   ├── preload.ts  # Preload script
    │   ├── App.tsx     # Main React component
    │   ├── stores/     # Zustand state
    │   │   └── useAppStore.ts
    │   └── tabs/       # Tab components
    │       ├── VehicleInfoTab.tsx
    │       ├── ConnectTab.tsx
    │       ├── LiveDataTab.tsx
    │       ├── StreamTab.tsx
    │       ├── DiagnosticsTab.tsx
    │       ├── TuningTab.tsx
    │       ├── RomToolsTab.tsx
    │       ├── FlashingTab.tsx
    │       ├── LogsTab.tsx
    │       └── SettingsTab.tsx
    ├── package.json
    ├── vite.config.ts
    └── tailwind.config.js
```

## Safety System

The application implements a multi-level safety system:

1. **ReadOnly**: View data only
2. **Simulate**: Test changes without applying
3. **LiveApply**: Apply changes to ECU
4. **Flash**: Enable ROM flashing

Each level requires explicit arming with confirmation dialogs and parameter validation.

## Development

- Rust core uses N-API for Node.js integration
- TypeScript throughout for type safety
- Zustand for React state management
- Tailwind CSS for styling with Mazda red accent theme
- PostgreSQL with Prisma for data persistence

## License

MIT
