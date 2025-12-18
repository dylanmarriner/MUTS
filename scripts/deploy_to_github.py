#!/usr/bin/env python3
"""
GitHub Deployment Script for MUTS Enterprise
Prepares and pushes the codebase to GitHub organization
"""

import os
import sys
import subprocess
import json
from pathlib import Path

# Configuration
GITHUB_ORG = "muts-enterprise"
REPO_NAME = "muts"
GITHUB_URL = f"git@github.com:{GITHUB_ORG}/{REPO_NAME}.git"

def run_command(cmd, cwd=None, check=True):
    """Run a shell command"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result

def check_git_status():
    """Check git status and ensure clean state"""
    print("\n=== Checking Git Status ===")
    
    # Check if we're in a git repo
    if not Path(".git").exists():
        print("Initializing git repository...")
        run_command("git init")
    
    # Check current status
    status = run_command("git status --porcelain")
    if status.stdout.strip():
        print("\nUncommitted changes detected:")
        print(status.stdout)
        
        response = input("\nCommit these changes? (y/n): ")
        if response.lower() == 'y':
            run_command("git add .")
            run_command('git commit -m "feat: Add enterprise-grade features\n\n- JWT authentication with RBAC\n- Comprehensive audit logging\n- CI/CD pipeline with security scanning\n- Vehicle integration for Holden VF and VW Golf\n- Standalone installer with offline support"')
        else:
            print("Please commit changes before deploying")
            sys.exit(1)
    
    print("✅ Git repository is clean")

def setup_github_remote():
    """Setup GitHub remote"""
    print("\n=== Setting up GitHub Remote ===")
    
    # Check if remote exists
    remotes = run_command("git remote -v")
    if GITHUB_URL in remotes.stdout:
        print("✅ GitHub remote already configured")
    else:
        print(f"Adding GitHub remote: {GITHUB_URL}")
        run_command(f"git remote add origin {GITHUB_URL}")

def create_github_config():
    """Create GitHub configuration files"""
    print("\n=== Creating GitHub Configuration ===")
    
    # Create .github directory structure
    dirs = [
        ".github",
        ".github/workflows",
        ".github/ISSUE_TEMPLATE",
        ".github/PULL_REQUEST_TEMPLATE"
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    # Create CODEOWNERS
    codeowners = """# CODEOWNERS
# This file controls who is automatically requested for review
# when pull requests are opened.

# Global owners
* @muts-enterprise/admin-team

# Backend code
app/ @muts-enterprise/backend-team

# Frontend code
electron-app/ @muts-enterprise/frontend-team

# Security files
SECURITY.md @muts-enterprise/security-team
.github/workflows/ @muts-enterprise/devops-team

# Documentation
docs/ @muts-enterprise/docs-team
"""
    
    with open(".github/CODEOWNERS", "w") as f:
        f.write(codeowners)
    
    # Create issue template
    issue_template = """---
name: Bug Report
about: Create a report to help us improve
title: '[BUG] '
labels: bug
assignees: ''
---

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment:**
 - OS: [e.g. Windows 10, Ubuntu 20.04]
 - MUTS Version: [e.g. 2.0.0]
 - Vehicle Interface: [e.g. J2534, CAN]

**Additional context**
Add any other context about the problem here.
"""
    
    with open(".github/ISSUE_TEMPLATE/bug_report.md", "w") as f:
        f.write(issue_template)
    
    print("✅ GitHub configuration created")

def verify_enterprise_features():
    """Verify all enterprise features are in place"""
    print("\n=== Verifying Enterprise Features ===")
    
    required_files = [
        ".github/workflows/enterprise-ci.yml",
        "app/muts/auth/enterprise_auth.py",
        "app/muts/audit/audit_logger.py",
        "SECURITY.md",
        ".gitignore"
    ]
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ Missing: {file_path}")
            sys.exit(1)
    
    print("\n✅ All enterprise features verified")

def create_release_notes():
    """Create initial release notes"""
    print("\n=== Creating Release Notes ===")
    
    release_notes = """# MUTS Enterprise v2.0.0

## 🚀 Major Features

### Enterprise Authentication
- JWT-based authentication with refresh tokens
- Role-based access control (Admin, Technician, Viewer)
- SSO integration support (SAML, OIDC)
- Session management with timeout

### Security & Compliance
- Comprehensive audit logging with checksums
- AES-256 data encryption
- GDPR compliance features
- Security incident tracking

### Vehicle Integration
- Holden Commodore VF full support
- Volkswagen Golf Mk6 with DSG support
- Hybrid vehicle selector UI
- Real VIN-based vehicle profiles

### Developer Experience
- CI/CD pipeline with security scanning
- Automated testing and deployment
- Code quality checks
- Multi-platform build system

## 📦 Installation

### Windows Installer
- Download `MUTS Setup 2.0.0.exe`
- Run installer with administrator privileges
- Launch from Start Menu

### Portable Version
- Download `MUTS-Portable-2.0.0.zip`
- Extract to desired location
- Run `MUTS.exe`

### Build from Source
```bash
git clone https://github.com/muts-enterprise/muts.git
cd muts
python build.py
```

## 🔧 What's Changed

### Added
- Enterprise authentication system
- Audit logging framework
- GitHub Actions CI/CD
- Vehicle profile management
- Standalone installer

### Security
- All API endpoints require authentication
- Data encryption at rest
- Audit trail for all operations
- Security scanning in CI/CD

### Documentation
- Complete API documentation
- Security policy
- Installation guide
- Architecture overview

## 🐛 Known Issues

- None at release time

## 🙏 Acknowledgments

Thanks to all contributors who made this release possible!

## 🔗 Links

- [Documentation](https://github.com/muts-enterprise/muts/wiki)
- [Security Policy](https://github.com/muts-enterprise/muts/blob/main/SECURITY.md)
- [Issue Tracker](https://github.com/muts-enterprise/muts/issues)
"""
    
    with open("RELEASE_NOTES.md", "w") as f:
        f.write(release_notes)
    
    print("✅ Release notes created")

def push_to_github():
    """Push code to GitHub"""
    print("\n=== Pushing to GitHub ===")
    
    # Get current branch
    branch = run_command("git branch --show-current").stdout.strip()
    print(f"Current branch: {branch}")
    
    # Push to GitHub
    print(f"Pushing to {GITHUB_URL}...")
    run_command(f"git push -u origin {branch}")
    
    print("✅ Code pushed to GitHub")

def create_initial_release():
    """Create initial release on GitHub"""
    print("\n=== Creating Initial Release ===")
    
    # Use GitHub CLI if available
    try:
        run_command("gh release create v2.0.0 --title 'MUTS Enterprise v2.0.0' --notes-file RELEASE_NOTES.md")
        print("✅ Release created on GitHub")
    except:
        print("⚠️ GitHub CLI not found. Create release manually:")
        print(f"1. Go to: https://github.com/{GITHUB_ORG}/{REPO_NAME}/releases/new")
        print("2. Tag: v2.0.0")
        print("3. Title: MUTS Enterprise v2.0.0")
        print("4. Copy contents from RELEASE_NOTES.md")

def main():
    """Main deployment process"""
    print("="*60)
    print("MUTS ENTERPRISE - GitHub Deployment")
    print("="*60 + "\n")
    
    # Check prerequisites
    print("Checking prerequisites...")
    try:
        run_command("git --version")
        run_command("gh --version")
        print("✅ Git and GitHub CLI installed")
    except:
        print("❌ Please install Git and GitHub CLI first")
        sys.exit(1)
    
    # Execute deployment steps
    check_git_status()
    setup_github_remote()
    create_github_config()
    verify_enterprise_features()
    create_release_notes()
    push_to_github()
    create_initial_release()
    
    # Success
    print("\n" + "="*60)
    print("DEPLOYMENT COMPLETE!")
    print("="*60)
    print(f"\nRepository: https://github.com/{GITHUB_ORG}/{REPO_NAME}")
    print("\nNext steps:")
    print("1. Configure branch protection rules")
    print("2. Set up GitHub Apps for CI/CD")
    print("3. Configure organization security settings")
    print("4. Invite team members")
    print("="*60)

if __name__ == "__main__":
    main()
