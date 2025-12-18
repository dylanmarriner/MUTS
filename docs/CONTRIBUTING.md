# Contributing to MUTS

Thank you for your interest in contributing to MUTS! This document provides guidelines for contributors.

## Development Mode Only

**IMPORTANT**: All development must be done in DEV mode only. ECU writes are blocked in DEV mode for safety.

```bash
# Always set OPERATOR_MODE=dev in your .env file
OPERATOR_MODE=dev
```

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a feature branch
4. Make your changes
5. Test thoroughly
6. Submit a pull request

```bash
git clone https://github.com/yourusername/MUTS.git
cd MUTS
git checkout -b feature/your-feature-name
```

## Development Setup

### Prerequisites
- Node.js 18+
- Rust 1.70+
- Git

### Install Dependencies
```bash
# Backend
cd backend
npm install

# Desktop UI
cd ../muts-desktop/electron-ui
npm install

# Rust Core
cd ../rust-core
cargo build
```

### Database Setup
```bash
cd backend
npx prisma generate
npx prisma db push
```

## Code Standards

### TypeScript
- Use strict TypeScript settings
- Provide types for all functions
- Avoid `any` type
- Use interfaces for data structures

### Rust
- Follow rustfmt formatting
- Use clippy for linting
- Document public functions
- Handle errors properly

### React/JSX
- Use functional components
- Follow React hooks rules
- Use TypeScript for props
- Keep components small and focused

## Testing

### Unit Tests
```bash
# Backend tests
cd backend
npm test

# Rust tests
cd muts
cargo test
```

### Integration Tests
- Test all API endpoints
- Verify safety controls
- Check error handling
- Test with and without hardware

## Safety Requirements

### No ECU Writes in DEV
- All write operations must be blocked in DEV mode
- Verify this before submitting PR
- Tests must confirm write blocking

### No Fake Data
- Never show fake data as real
- Use NOT_CONNECTED when no interface
- Mark stale data explicitly
- Tests must verify data truthfulness

### Error Handling
- All errors must be handled gracefully
- No silent failures
- Log errors appropriately
- User-friendly error messages

## Pull Request Process

1. Update documentation
2. Add tests for new features
3. Ensure all tests pass
4. Update CHANGELOG.md
5. Submit PR with clear description

### PR Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation
- [ ] Refactoring

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Safety controls verified

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
```

## Release Process

Only maintainers should:
- Tag releases
- Build installers
- Update version numbers
- Publish to GitHub Releases

## Security

If you find a security vulnerability:
1. Do NOT open a public issue
2. Email security@muts.dev
3. Wait for response
4. Follow disclosure process

See [SECURITY.md](SECURITY.md) for details.

## Getting Help

- GitHub Issues: Report bugs and request features
- GitHub Discussions: Ask questions and share ideas
- Documentation: Check existing docs first

## Code of Conduct

Be respectful and professional:
- Welcome new contributors
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other community members

## License

By contributing, you agree your code will be licensed under the MIT License.
