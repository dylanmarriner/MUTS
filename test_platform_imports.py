#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MUTS Platform Import Test
Tests all 90+ platform files for import errors and dependencies
"""

import sys
import os
import importlib.util
import traceback
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_file_import(file_path):
    """Test if a Python file can be imported successfully"""
    try:
        # Get module name from file path
        module_name = file_path.stem
        
        # Load the module
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None:
            return False, f"Could not create spec for {module_name}"
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        return True, f"Successfully imported {module_name}"
        
    except ImportError as e:
        return False, f"Import error in {file_path.name}: {e}"
    except SyntaxError as e:
        return False, f"Syntax error in {file_path.name}: {e}"
    except Exception as e:
        return False, f"Error in {file_path.name}: {e}"

def main():
    """Test all platform files"""
    print("=== MUTS PLATFORM IMPORT TEST ===\n")
    
    # Define platform file patterns
    platform_files = {
        'versa': list(Path('.').glob('versa*.py')),
        'muts': list(Path('.').glob('muts*.py')),
        'mpsrom': list(Path('.').glob('mpsrom*.py')),
        'mds': list(Path('.').glob('mds*.py')),
        'cobb': list(Path('.').glob('cobb*.py')),
        'add': list(Path('.').glob('add*.py')),
    }
    
    results = {}
    total_files = 0
    passed_files = 0
    
    for platform, files in platform_files.items():
        print(f"Testing {platform.upper()} files...")
        platform_results = []
        
        for file_path in sorted(files):
            if file_path.name == 'test_integration.py':
                continue  # Skip test files
                
            total_files += 1
            success, message = test_file_import(file_path)
            platform_results.append((file_path.name, success, message))
            
            if success:
                passed_files += 1
                print(f"  ✅ {file_path.name}")
            else:
                print(f"  ❌ {file_path.name}: {message}")
        
        results[platform] = platform_results
        print()
    
    # Summary
    print("=== IMPORT TEST SUMMARY ===")
    print(f"Total files tested: {total_files}")
    print(f"Passed: {passed_files}")
    print(f"Failed: {total_files - passed_files}")
    print(f"Success rate: {(passed_files/total_files)*100:.1f}%")
    
    # Show failed files
    failed_files = []
    for platform, platform_results in results.items():
        for filename, success, message in platform_results:
            if not success:
                failed_files.append((platform, filename, message))
    
    if failed_files:
        print(f"\n=== FAILED FILES ({len(failed_files)}) ===")
        for platform, filename, message in failed_files:
            print(f"❌ {platform}/{filename}: {message}")
    
    return len(failed_files) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
