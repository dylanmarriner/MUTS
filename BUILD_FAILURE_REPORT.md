# Build Failure Report

This document explains why MUTS cannot be built from a fresh clone and provides workarounds where possible.

## Build Status: 🔴 BROKEN

**Overall Build Sanity Score: 20%**

The project requires significant manual intervention and code changes to build successfully.

## Component Status

### 1. Backend (Node.js/TypeScript) - ❌ BROKEN

#### Issues
- No `.env` file provided
- Requires manual PostgreSQL setup
- Prisma migrations not included

#### Error Messages
```
Error: DATABASE_URL not found
Error: Can't reach database server
Error: No migration found
```

#### Workaround
```bash
# 1. Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# 2. Create database
sudo -u postgres createdb muts_db

# 3. Create .env file
cp backend/.env.example backend/.env
# Edit .env with your database credentials

# 4. Generate Prisma client
cd backend
npx prisma generate

# 5. Push schema
npx prisma db push

# 6. Build
npm run build
```

### 2. Rust Core - ❌ BROKEN

#### Issues
- Missing `build.rs` for NAPI
- Platform-specific dependencies without feature flags
- No target configuration for Node.js addon

#### Error Messages
```
error: target "nodejs-addon" not found
error: couldn't find crate socketcan on Windows
error: napi_build::setup() not called
```

#### Workaround
```bash
# 1. Create build.rs
cd muts-desktop/rust-core
cat > build.rs << 'EOF'
fn main() {
    napi_build::setup();
}
EOF

# 2. Update Cargo.toml
# Add feature flags for platform-specific deps:
# [features]
# default = ["linux"]
# linux = ["socketcan"]
# windows = ["j2534"]

# 3. Install NAPI tools
cargo install napi-cli

# 4. Build
napi build --platform --target nodejs-addon
```

### 3. Electron App - ❌ BROKEN

#### Issues
- Main process TypeScript not configured
- No build step for main.js
- Assumes pre-built Rust native module

#### Error Messages
```
Error: Cannot find module './dist/main.js'
Error: Electron failed to start
Error: Native module not found
```

#### Workaround
```bash
# 1. Configure TypeScript for main process
cd muts-desktop/electron-ui
cat > tsconfig.main.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "CommonJS",
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true
  },
  "include": ["src/main.ts"]
}
EOF

# 2. Update package.json scripts
# "build:main": "tsc -p tsconfig.main.json"
# "build": "npm run build:main && npm run build:renderer"

# 3. Build main process
npx tsc -p tsconfig.main.json

# 4. Build renderer
npm run build:renderer

# 5. Build Rust core first (see above)
```

## Complete Build Instructions

### Prerequisites
```bash
# System dependencies
sudo apt-get update
sudo apt-get install -y postgresql nodejs npm python3 python3-pip

# Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env

# Python tools
pip install maturin

# Node dependencies (in each directory)
npm install
```

### Step-by-Step Build

```bash
# 1. Clone repository
git clone https://github.com/your-org/muts.git
cd muts

# 2. Setup database
sudo -u postgres createdb muts_db
cp backend/.env.example backend/.env
# Edit backend/.env with database URL

# 3. Build backend
cd backend
npm install
npx prisma generate
npx prisma db push
npm run build
cd ..

# 4. Fix and build Rust core
cd muts-desktop/rust-core
# Apply workarounds from above
napi build --platform --target nodejs-addon
cd ..

# 5. Fix and build Electron app
cd electron-ui
# Apply workarounds from above
npm run build
cd ../..

# 6. Run application
cd muts-desktop/electron-ui
npm start
```

## Root Causes

### 1. Missing Configuration Files
- No `.env` file for environment
- No `build.rs` for Rust NAPI
- No TypeScript config for main process

### 2. Platform Assumptions
- Assumes PostgreSQL installed locally
- Assumes Linux development environment
- Assumes specific directory structure

### 3. Dependency Issues
- Platform-specific crates not gated
- Missing build tools documentation
- Circular dependencies (Rust needs Node, Node needs Rust)

### 4. Documentation Gaps
- No setup prerequisites listed
- No troubleshooting guide
- No platform-specific instructions

## Fixes Needed

### Immediate (Critical)
1. Add default SQLite database option
2. Create proper build.rs for NAPI
3. Add feature flags for platform code
4. Configure TypeScript for main process

### Short Term
1. Add Docker development environment
2. Create setup scripts for each platform
3. Add CI/CD pipeline
4. Improve documentation

### Long Term
1. Simplify build process
2. Use monorepo tooling
3. Add automated testing
4. Create installer packages

## Platform-Specific Issues

### Linux
- ✅ Most compatible
- ❌ Requires manual PostgreSQL
- ❌ SocketCAN permissions

### Windows
- ❌ SocketCAN not available
- ❌ Different build tools needed
- ❌ Path separators wrong

### macOS
- ❌ SocketCAN not available
- ❌ Different PostgreSQL setup
- ❌ Codesigning required

## Testing the Build

### Automated Tests
```bash
# Backend tests
cd backend
npm test  # Currently fails - no tests defined

# Rust tests
cd muts-desktop/rust-core
cargo test  # May fail due to platform deps

# Integration tests
# Not implemented
```

### Manual Verification
1. Backend starts without errors
2. Database connection works
3. Rust native module loads
4. Electron app launches
5. UI displays correctly

## Common Build Errors

### Database Connection Failed
```
Error: connect ECONNREFUSED 127.0.0.1:5432
```
**Solution**: Install and start PostgreSQL

### Native Module Not Found
```
Error: Cannot find module 'muts_core.node'
```
**Solution**: Build Rust core with NAPI

### TypeScript Compilation Error
```
Error: Cannot find module './dist/main.js'
```
**Solution**: Compile main process TypeScript

### Permission Denied
```
Error: EACCES: permission denied
```
**Solution**: Check file permissions, use sudo if needed

## Getting Help

### Debug Mode
```bash
# Enable verbose logging
DEBUG=* npm start

# Rust debug build
cargo build

# TypeScript debug
npx tsc --traceResolution
```

### Community Support
- GitHub Issues: [Create issue](https://github.com/your-org/muts/issues)
- Documentation: [Check docs folder](/docs)
- Troubleshooting: [Known Issues](KNOWN_CRITICAL_ISSUES.md)

## Contributing Fixes

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Pull Request Template
```markdown
## Fix Type
- [ ] Bug fix
- [ ] Documentation
- [ ] Build system

## Testing
- [ ] Tested on Linux
- [ ] Tested on Windows
- [ ] Tested on macOS
- [ ] Fresh clone test passed

## Verification
- [ ] Backend builds
- [ ] Rust core builds
- [ ] Electron app builds
- [ ] Application starts
```

---

**Remember**: The build system is currently broken. These workarounds are temporary until proper fixes are implemented.
