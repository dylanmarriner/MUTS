# MUTS Setup Guide

## Prerequisites
- Node.js v18+
- Python 3.12
- Rust 1.70+
- PostgreSQL 15+

## Installation
```bash
git clone https://github.com/dylanmarriner/MUTS.git
cd MUTS

# Install dependencies
npm install
pip install -e .[dev]

# Set up environment variables
cp .env.example .env

# Initialize database
prisma migrate dev
```

## Running Locally
```bash
# Start backend
cd backend && npm run dev

# Start frontend
cd muts-ui && npm run dev

# Start rust-core
cd muts-desktop/rust-core && cargo run
```
