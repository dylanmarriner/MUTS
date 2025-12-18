# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 1.0.x   | ✅                 |

## Reporting a Vulnerability

**IMPORTANT**: Do NOT open a public issue for security vulnerabilities!

### How to Report

1. **Email**: security@muts.dev
2. **Subject**: Security Vulnerability - [Brief Description]
3. **Include**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Your contact information

### Response Timeline

- **Initial Response**: Within 48 hours
- **Detailed Assessment**: Within 7 days
- **Resolution**: As soon as feasible, based on severity

### What Happens Next

1. We'll acknowledge receipt within 48 hours
2. We'll investigate and assess the impact
3. We'll work on a fix
4. We'll coordinate disclosure with you
5. We'll release security update if needed

## Security Model

MUTS is designed with multiple security layers:

### Operator Mode Controls
- **DEV Mode**: All ECU writes blocked
- **WORKSHOP Mode**: Writes allowed with authorization
- **LAB Mode**: Writes allowed with debug features

### Authentication Requirements
- Technician authentication required for writes
- Job tracking enforced
- Session management with ARM flow

### Data Protection
- No fake data displayed as real
- Explicit NOT_CONNECTED indicators
- STALE data marking after 2 seconds

### Audit Trails
- All operations logged
- Technician and job attribution
- Timestamps and success/failure status

## ECU Security Considerations

⚠️ **WARNING**: MUTS can write to vehicle ECUs. This carries inherent risks:

- **Vehicle Damage**: Incorrect tuning can damage engine
- **Safety Risks**: Unsafe modifications can be dangerous
- **Warranty Impact**: May void vehicle warranty
- **Legal Compliance**: Must comply with local laws

### Mitigations
- All writes require explicit authorization
- Safety limits enforced where possible
- Full audit trail for accountability
- Professional use only (not for end consumers)

## Best Practices

### For Users
- Always backup original ECU data
- Use in WORKSHOP mode for real vehicles
- Follow proper tuning procedures
- Keep software updated

### For Developers
- Always work in DEV mode
- Never commit secrets
- Follow security guidelines in CONTRIBUTING.md
- Report vulnerabilities responsibly

## Threat Model

### Considered Threats
1. **Unauthorized ECU Writes**
   - Mitigated by operator modes and authentication
   - Blocked in DEV mode

2. **Data Integrity**
   - Mitigated by checksums and verification
   - No fake data policy

3. **Privilege Escalation**
   - Mitigated by role-based access
   - Technician authentication required

4. **Audit Trail Tampering**
   - Mitigated by immutable logging
   - Database protections

### Out of Scope
- Physical attacks on connected vehicles
- Malicious intent by authorized technicians
- Social engineering attacks

## Security Features

### Write Protection
```typescript
// Example: Write blocked in DEV mode
if (operatorMode === 'DEV') {
  throw new Error('ECU writes not allowed in DEV mode');
}
```

### Authentication
```typescript
// Example: Technician required
if (!technician || !job) {
  throw new Error('Technician and job required');
}
```

### Data Validation
```typescript
// Example: No fake data
if (!interfaceConnected) {
  return 'NOT_CONNECTED';
}
```

## Security Updates

Security updates will be:
- Released as needed
- Backported to supported versions
- Announced in release notes
- Coordinated with reporters

## Acknowledgments

We thank security researchers who help keep MUTS safe. All valid reports will be acknowledged in release notes (with permission).

## Legal Disclaimer

This security policy is provided without warranty. Users must comply with all applicable laws and regulations.
