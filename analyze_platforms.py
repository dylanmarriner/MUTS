#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MUTS Platform Analysis and Prioritization Tool
Analyzes the 87 broken platform files to create an implementation strategy
"""

import sys
import os
import re
from pathlib import Path
from collections import defaultdict

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def analyze_file_issues(file_path):
    """Analyze specific issues in a Python file"""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Check for syntax issues
        try:
            compile(content, str(file_path), 'exec')
        except SyntaxError as e:
            issues.append(f"Syntax Error: {e}")
        except Exception:
            pass  # Other compilation errors are normal for imports
        
        # Check for relative imports
        relative_imports = re.findall(r'from\s+\.\.+\s+import', content)
        if relative_imports:
            issues.append(f"Relative imports: {len(relative_imports)} found")
        
        # Check for missing core modules
        missing_core = re.findall(r'from\s+(core\.|src\.core\.)', content)
        if missing_core:
            issues.append(f"Missing core modules: {len(missing_core)} references")
        
        # Check for common missing dependencies
        missing_deps = []
        common_deps = ['numpy', 'torch', 'matplotlib', 'crcmod', 'cryptography', 'serial', 'flask', 'usb']
        for dep in common_deps:
            if f'import {dep}' in content or f'from {dep}' in content:
                missing_deps.append(dep)
        if missing_deps:
            issues.append(f"Dependencies: {', '.join(missing_deps)}")
        
        # Count classes and functions
        class_count = len(re.findall(r'^class\s+\w+', content, re.MULTILINE))
        func_count = len(re.findall(r'^def\s+\w+', content, re.MULTILINE))
        
        return {
            'issues': issues,
            'class_count': class_count,
            'func_count': func_count,
            'line_count': len(lines),
            'file_size': len(content)
        }
        
    except Exception as e:
        return {
            'issues': [f"File read error: {e}"],
            'class_count': 0,
            'func_count': 0,
            'line_count': 0,
            'file_size': 0
        }

def categorize_platform_files():
    """Categorize platform files by complexity and priority"""
    platforms = {
        'versa': list(Path('.').glob('versa*.py')),
        'muts': list(Path('.').glob('muts*.py')),
        'mpsrom': list(Path('.').glob('mpsrom*.py')),
        'mds': list(Path('.').glob('mds*.py')),
        'cobb': list(Path('.').glob('cobb*.py')),
        'add': list(Path('.').glob('add*.py')),
    }
    
    analysis = {}
    
    for platform, files in platforms.items():
        platform_analysis = []
        
        for file_path in sorted(files):
            if file_path.name in ['test_integration.py', 'test_core_system.py', 'test_platform_imports.py']:
                continue
                
            file_analysis = analyze_file_issues(file_path)
            file_analysis['filename'] = file_path.name
            file_analysis['path'] = str(file_path)
            
            # Calculate complexity score
            complexity = (file_analysis['class_count'] * 3 + 
                         file_analysis['func_count'] * 1 + 
                         len(file_analysis['issues']) * 2)
            file_analysis['complexity_score'] = complexity
            
            platform_analysis.append(file_analysis)
        
        # Sort by complexity (easiest first)
        platform_analysis.sort(key=lambda x: x['complexity_score'])
        analysis[platform] = platform_analysis
    
    return analysis

def create_implementation_strategy(analysis):
    """Create a prioritized implementation strategy"""
    print("=== MUTS PLATFORM IMPLEMENTATION STRATEGY ===\n")
    
    # Working files (baseline)
    working_files = ['versa1.py', 'muts3.py', 'muts6.py']
    print(f"✅ ALREADY WORKING: {len(working_files)} files")
    for f in working_files:
        print(f"   - {f}")
    print()
    
    # Analyze each platform
    total_files = 0
    total_issues = 0
    
    for platform, files in analysis.items():
        print(f"=== {platform.upper()} PLATFORM ===")
        
        easy_files = [f for f in files if len(f['issues']) <= 2]
        medium_files = [f for f in files if 3 <= len(f['issues']) <= 5]
        hard_files = [f for f in files if len(f['issues']) > 5]
        
        print(f"  Total files: {len(files)}")
        print(f"  Easy (≤2 issues): {len(easy_files)}")
        print(f"  Medium (3-5 issues): {len(medium_files)}")
        print(f"  Hard (>5 issues): {len(hard_files)}")
        
        total_files += len(files)
        total_issues += sum(len(f['issues']) for f in files)
        
        # Show easiest files first
        if easy_files:
            print(f"\n  🟢 EASIEST FILES TO FIX:")
            for f in easy_files[:3]:  # Show top 3 easiest
                print(f"     {f['filename']}: {len(f['issues'])} issues, {f['class_count']} classes")
        
        print()
    
    print(f"=== OVERALL SUMMARY ===")
    print(f"Total platform files: {total_files}")
    print(f"Total issues to fix: {total_issues}")
    print(f"Average issues per file: {total_issues/total_files:.1f}")
    
    # Create priority recommendations
    print(f"\n=== IMPLEMENTATION PRIORITY RECOMMENDATIONS ===")
    
    # Priority 1: Easy files across all platforms
    all_easy = []
    for platform, files in analysis.items():
        all_easy.extend([(platform, f) for f in files if len(f['issues']) <= 2])
    
    all_easy.sort(key=lambda x: x[1]['complexity_score'])
    
    print("🥇 PRIORITY 1 - QUICK WINS (Easy files, high impact):")
    for platform, f in all_easy[:10]:  # Top 10 easiest
        print(f"   {platform}/{f['filename']}: {len(f['issues'])} issues, {f['class_count']} classes")
    
    # Priority 2: Key platforms (versa, cobb, mds)
    key_platforms = ['versa', 'cobb', 'mds']
    print(f"\n🥈 PRIORITY 2 - KEY PLATFORMS (versa, cobb, mds):")
    for platform in key_platforms:
        if platform in analysis:
            files = analysis[platform][:5]  # Top 5 easiest from each key platform
            print(f"   {platform.upper()}:")
            for f in files:
                print(f"     - {f['filename']}: {len(f['issues'])} issues")
    
    # Priority 3: High-value files (many classes/functions)
    high_value = []
    for platform, files in analysis.items():
        for f in files:
            if f['class_count'] >= 3 or f['func_count'] >= 10:
                high_value.append((platform, f))
    
    high_value.sort(key=lambda x: x[1]['complexity_score'])
    
    print(f"\n🥉 PRIORITY 3 - HIGH VALUE FILES (Most functionality):")
    for platform, f in high_value[:10]:
        print(f"   {platform}/{f['filename']}: {f['class_count']} classes, {f['func_count']} functions")
    
    return analysis

def main():
    """Main analysis function"""
    analysis = categorize_platform_files()
    strategy = create_implementation_strategy(analysis)
    
    print(f"\n=== RECOMMENDATION ===")
    print("Start with PRIORITY 1 files (quick wins) to build momentum.")
    print("Then focus on PRIORITY 2 key platforms (versa, cobb, mds).")
    print("Finally implement PRIORITY 3 high-value files for maximum functionality.")
    print("\nThis approach will deliver working platforms incrementally")
    print("rather than attempting to fix all 87 files simultaneously.")
    
    return strategy

if __name__ == "__main__":
    strategy = main()
