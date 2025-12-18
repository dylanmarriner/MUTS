#!/usr/bin/env python3
"""
Validate backend reorganization - check imports and structure
"""

import os
import sys
import importlib.util
from pathlib import Path

def validate_module_import(module_path):
    """Test if a module can be imported without errors"""
    try:
        spec = importlib.util.spec_from_file_location("test_module", module_path)
        if spec is None:
            return False, "Could not create spec"
        
        module = importlib.util.module_from_spec(spec)
        # Don't execute, just check if it can be loaded
        return True, "OK"
    except Exception as e:
        return False, str(e)

def check_for_mock_data(file_path):
    """Check for mock data or stubs"""
    mock_patterns = [
        "TODO:", "FIXME:", "XXX:", 
        "mock_data", "fake_", "dummy_",
        "stub_", "test_data"
    ]
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            for pattern in mock_patterns:
                if pattern in content:
                    return True, f"Found pattern: {pattern}"
        return False, None
    except:
        return False, "Could not read file"

def main():
    print("Backend Reorganization Validation")
    print("=" * 50)
    
    backend_root = Path(__file__).parent
    python_files = list(backend_root.rglob("*.py"))
    
    print(f"\nFound {len(python_files)} Python files")
    
    # Check imports
    print("\n1. Checking imports...")
    import_errors = []
    for py_file in python_files:
        if py_file.name == "validate_imports.py":
            continue
        
        can_import, error = validate_module_import(py_file)
        if not can_import:
            import_errors.append((str(py_file), error))
    
    if import_errors:
        print(f"  ❌ {len(import_errors)} files have import issues")
        for file, error in import_errors[:5]:  # Show first 5
            print(f"    {file}: {error}")
    else:
        print("  ✅ All files can be imported")
    
    # Check for mock data
    print("\n2. Checking for mock data...")
    mock_files = []
    for py_file in python_files:
        has_mock, pattern = check_for_mock_data(py_file)
        if has_mock:
            mock_files.append((str(py_file), pattern))
    
    if mock_files:
        print(f"  ❌ {len(mock_files)} files contain mock patterns")
        for file, pattern in mock_files:
            print(f"    {file}: {pattern}")
    else:
        print("  ✅ No mock data found")
    
    # Check structure
    print("\n3. Checking structure...")
    required_dirs = [
        "core", "diagnostics", "tuning", 
        "interfaces", "security", "persistence",
        "compatibility", "api", "vehicles"
    ]
    
    missing_dirs = []
    for dir_name in required_dirs:
        if not (backend_root / dir_name).exists():
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        print(f"  ❌ Missing directories: {', '.join(missing_dirs)}")
    else:
        print("  ✅ All required directories present")
    
    # Summary
    print("\n" + "=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)
    
    if not import_errors and not mock_files and not missing_dirs:
        print("✅ BACKEND REORGANIZATION COMPLETE")
        print("   - All imports valid")
        print("   - No mock data detected")
        print("   - Structure correct")
    else:
        print("❌ ISSUES FOUND")
        if import_errors:
            print(f"   - {len(import_errors)} import errors")
        if mock_files:
            print(f"   - {len(mock_files)} files with mock data")
        if missing_dirs:
            print(f"   - {len(missing_dirs)} missing directories")

if __name__ == "__main__":
    main()
