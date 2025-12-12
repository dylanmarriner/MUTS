# Known Critical Issues

This document lists all critical issues found during comprehensive audits of MUTS. These issues prevent safe operation and must be fixed before any production use.

## 🔴 Critical Safety Issues

### SAFETY-001: Synthetic Telemetry Data
**Impact**: CRITICAL - Shows fake data as real
**Location**: `muts-desktop/electron-ui/src/tabs/StreamTab.tsx`
**Details**:
- Generates random CAN frames and displays as real
- Users cannot distinguish real vs synthetic data
- Can lead to incorrect tuning decisions

**Audit Report**: [runtime_data_truth_report.json](build_artifacts/runtime_data_truth_report.json)

### SAFETY-002: Mock Safety Monitoring
**Impact**: CRITICAL - Safety checks use fake values
**Location**: `backend/src/modules/tuning-platform/safety-orchestrator.ts`
**Details**:
- `captureSafetySnapshot()` returns mock data
- Safety violations cannot be detected
- Auto-revert based on fake conditions

**Audit Report**: [ecu_write_path_audit.json](build_artifacts/ecu_write_path_audit.json)

### BUILD-001: Build System Broken
**Impact**: HIGH - Cannot build from fresh clone
**Score**: 20% build sanity
**Details**:
- Backend requires manual database setup
- Rust core missing NAPI configuration
- Electron main process not compiled
- Hardcoded local paths

**Audit Report**: [build_sanity_report.md](build_artifacts/build_sanity_report.md)

### PERF-001: Non-Deterministic Flash Operations
**Impact**: CRITICAL - Flash can fail without recovery
**Location**: `muts-desktop/rust-core/src/lib.rs`
**Details**:
- Flash tasks spawned detached (no control)
- No timing guarantees
- Cannot abort mid-operation
- No recovery procedures

**Audit Report**: [performance_timing_report.md](build_artifacts/performance_timing_report.md)

## 🟠 High Priority Issues

### FFI-001: Memory Safety Issues
**Impact**: HIGH - Potential crashes or corruption
**Location**: Rust-Node FFI boundary
**Details**:
- No lifetime guarantees
- Error handling incomplete
- Potential memory leaks
- Thread safety concerns

**Audit Report**: [ffi_contract_report.md](build_artifacts/ffi_contract_report.md)

### ADD-001: ADD Policy Violations
**Impact**: MEDIUM - AI could bypass safety (theoretical)
**Location**: `backend/src/modules/add/`
**Details**:
- ADD has no write capability (good)
- But decision heuristics not fully validated
- Confidence thresholds not enforced
- Risk assessment incomplete

**Audit Report**: [add_decision_policy.json](build_artifacts/add_decision_policy.json)

### FLASH-001: No Recovery Procedures
**Impact**: HIGH - Failed operations brick ECU
**Details**:
- No rollback implementation
- No backup procedures
- No bootloader detection
- No recovery UI

**Audit Report**: [failure_recovery_matrix.md](build_artifacts/failure_recovery_matrix.md)

## 🟡 Medium Priority Issues

### UI-001: Missing Error Handling
**Impact**: MEDIUM - Poor user experience
**Details**:
- Errors not properly displayed
- No error recovery guidance
- Silent failures possible

### DOC-001: Incomplete Documentation
**Impact**: LOW - Hard to use
**Details**:
- API documentation missing
- Setup guide incomplete
- Examples not working

### PERF-002: Performance Issues
**Impact**: MEDIUM - System unresponsive
**Details**:
- UI thread blocking
- No backpressure handling
- Event queue overflow

## 🔵 Low Priority Issues

### UI-002: Visual Polish
**Impact**: LOW - Cosmetic
**Details**:
- Inconsistent styling
- Missing animations
- Poor responsive design

## Issue Status Matrix

| Issue | Status | Owner | Target Fix |
|-------|--------|-------|------------|
| SAFETY-001 | Open | TBD | v0.2.0 |
| SAFETY-002 | Open | TBD | v0.2.0 |
| BUILD-001 | In Progress | TBD | v0.1.1 |
| PERF-001 | Open | TBD | v0.2.0 |
| FFI-001 | Open | TBD | v0.1.2 |
| ADD-001 | Open | TBD | v0.1.3 |
| FLASH-001 | Open | TBD | v0.2.0 |

## Fix Priority Order

### Immediate (Block Release)
1. BUILD-001 - Must build from fresh clone
2. SAFETY-001 - Remove synthetic data
3. SAFETY-002 - Implement real safety monitoring

### Short Term (v0.1.x)
1. PERF-001 - Fix flash determinism
2. FFI-001 - Fix memory safety
3. FLASH-001 - Add recovery procedures

### Medium Term (v0.2.0)
1. ADD-001 - Complete ADD validation
2. UI-001 - Add error handling
3. PERF-002 - Optimize performance

## Testing Required

### Safety Tests
- [ ] All synthetic data removed
- [ ] Safety monitoring functional
- [ ] Flash recovery tested
- [ ] Memory safety verified

### Build Tests
- [ ] Fresh clone builds
- [ ] All platforms build
- [ ] No manual steps required
- [ ] CI/CD functional

### Integration Tests
- [ ] End-to-end scenarios
- [ ] Error conditions
- [ ] Performance under load
- [ ] Recovery procedures

## Risk Assessment

### Current Risk Level: 🔴 CRITICAL

**Do NOT use on vehicles under any circumstances.**

### Risk Reduction Plan
1. Fix all critical safety issues
2. Implement comprehensive testing
3. Add safety certifications
4. External security audit

## Contributing to Fixes

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Safety Critical Fixes
- Require peer review
- Must include tests
- Documentation required
- Risk assessment mandatory

### Reporting New Issues
1. Check existing issues
2. Create detailed report
3. Include reproduction steps
4. Assess impact level

---

**Remember**: This is experimental software. Safety is the top priority.
