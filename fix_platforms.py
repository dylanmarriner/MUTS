#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MUTS Platform Fix Script
Systematically fixes common issues across platform files
"""

import sys
import os
import re
from pathlib import Path
from typing import List, Dict, Tuple

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

class PlatformFixer:
    """Systematically fixes common platform file issues"""
    
    def __init__(self):
        self.fixes_applied = 0
        self.files_fixed = 0
        
    def fix_relative_imports(self, content: str) -> Tuple[str, int]:
        """Fix relative imports to absolute imports"""
        fixes = 0
        
        # Common relative import patterns to fix
        patterns = [
            (r'from\s+\.+\s+import\s+(.+)', r'from \1'),
            (r'from\s+\.+\s+core\s+import', 'from core import'),
            (r'from\s+\.+\s+utils\s+import', 'from utils import'),
            (r'from\s+\.+\s+gui\s+import', 'from gui import'),
            (r'from\s+\.+\s+muts\s+import', 'from muts import'),
        ]
        
        for pattern, replacement in patterns:
            matches = re.findall(pattern, content)
            if matches:
                content = re.sub(pattern, replacement, content)
                fixes += len(matches)
        
        return content, fixes
    
    def fix_missing_core_imports(self, content: str) -> Tuple[str, int]:
        """Fix missing core module imports"""
        fixes = 0
        
        # Fix src.core references to core
        content = re.sub(r'from\s+src\.core\s+', 'from core ', content)
        content = re.sub(r'from\s+src\.muts\.core\s+', 'from muts.core ', content)
        
        # Fix core.diagnostic_protocols to core.ecu_communication
        content = re.sub(r'from\s+core\.diagnostic_protocols', 'from core.ecu_communication', content)
        
        if 'src.core' in content or 'src.muts.core' in content:
            fixes += 1
            
        return content, fixes
    
    def fix_syntax_errors(self, content: str) -> Tuple[str, int]:
        """Fix common syntax errors"""
        fixes = 0
        
        # Fix unmatched parentheses (common in legacy files)
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            original_line = line
            
            # Fix common unmatched parenthesis patterns
            if line.count('(') != line.count(')'):
                # Add missing parentheses at end of line if it looks like a function call
                if line.strip().endswith(':') and line.count('(') > line.count(')'):
                    line = line.rstrip() + ')'
                    fixes += 1
            
            fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        return content, fixes
    
    def add_standard_imports(self, content: str, filename: str) -> Tuple[str, int]:
        """Add standard imports for ECU communication files"""
        fixes = 0
        
        # Check if this looks like an ECU communication file
        if ('ECU' in content or 'ecu' in content or 'CAN' in content or 'can' in content) and \
           'from core.ecu_communication import' not in content:
            
            # Add core imports at the top
            import_lines = [
                'from core.ecu_communication import ECUCommunicator, ECUResponse, ECUState',
                'from core.safety_validator import get_safety_validator',
                'from utils.logger import get_logger'
            ]
            
            lines = content.split('\n')
            insert_pos = 0
            
            # Find the position after existing imports
            for i, line in enumerate(lines):
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    insert_pos = i + 1
                elif line.strip() and not (line.strip().startswith('import ') or line.strip().startswith('from ') or line.strip().startswith('#')):
                    break
            
            # Insert imports
            for import_line in import_lines:
                if import_line not in content:
                    lines.insert(insert_pos, import_line)
                    insert_pos += 1
                    fixes += 1
            
            content = '\n'.join(lines)
        
        return content, fixes
    
    def fix_file(self, file_path: Path) -> Dict[str, any]:
        """Fix issues in a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                original_content = f.read()
            
            content = original_content
            total_fixes = 0
            fix_details = []
            
            # Apply fixes systematically
            content, import_fixes = self.fix_relative_imports(content)
            if import_fixes > 0:
                total_fixes += import_fixes
                fix_details.append(f"Fixed {import_fixes} relative imports")
            
            content, core_fixes = self.fix_missing_core_imports(content)
            if core_fixes > 0:
                total_fixes += core_fixes
                fix_details.append(f"Fixed {core_fixes} core import issues")
            
            content, syntax_fixes = self.fix_syntax_errors(content)
            if syntax_fixes > 0:
                total_fixes += syntax_fixes
                fix_details.append(f"Fixed {syntax_fixes} syntax errors")
            
            content, std_fixes = self.add_standard_imports(content, file_path.name)
            if std_fixes > 0:
                total_fixes += std_fixes
                fix_details.append(f"Added {std_fixes} standard imports")
            
            # Write fixed content back
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.files_fixed += 1
            
            self.fixes_applied += total_fixes
            
            return {
                'success': True,
                'fixes_applied': total_fixes,
                'fix_details': fix_details,
                'file_size': len(content)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'fixes_applied': 0,
                'fix_details': []
            }
    
    def fix_priority_files(self) -> Dict[str, any]:
        """Fix PRIORITY 1 quick win files"""
        print("=== FIXING PRIORITY 1 QUICK WIN FILES ===\n")
        
        # Priority 1 files from analysis (0-1 issues each)
        priority_files = [
            'add13.py', 'add17.py', 'add20.py', 'versa10.py', 'cobb4.py',
            'add24.py', 'versa14.py', 'versa15.py', 'versa2.py', 'mds14.py'
        ]
        
        results = []
        
        for filename in priority_files:
            file_path = Path(filename)
            if file_path.exists():
                print(f"Fixing {filename}...")
                result = self.fix_file(file_path)
                
                if result['success']:
                    if result['fixes_applied'] > 0:
                        print(f"  ✅ Fixed: {', '.join(result['fix_details'])}")
                    else:
                        print(f"  ✅ No fixes needed")
                    results.append((filename, True, result['fixes_applied']))
                else:
                    print(f"  ❌ Error: {result['error']}")
                    results.append((filename, False, 0))
            else:
                print(f"  ⚠️  File not found: {filename}")
                results.append((filename, False, 0))
        
        return {
            'total_files': len(priority_files),
            'files_fixed': self.files_fixed,
            'total_fixes': self.fixes_applied,
            'results': results
        }
    
    def fix_key_platforms(self) -> Dict[str, any]:
        """Fix key platform files (versa, cobb, mds)"""
        print("\n=== FIXING KEY PLATFORM FILES ===\n")
        
        key_platforms = {
            'versa': ['versa11.py', 'versa12.py', 'versa13.py', 'versa16.py', 'versa18.py'],
            'cobb': ['cobb1.py', 'cobb2.py', 'cobb3.py', 'cobb5.py', 'cobb6.py'],
            'mds': ['mds1.py', 'mds2.py', 'mds3.py', 'mds4.py', 'mds5.py']
        }
        
        results = []
        
        for platform, files in key_platforms.items():
            print(f"Fixing {platform.upper()} platform files...")
            
            for filename in files:
                file_path = Path(filename)
                if file_path.exists():
                    result = self.fix_file(file_path)
                    
                    if result['success']:
                        if result['fixes_applied'] > 0:
                            print(f"  ✅ {filename}: {', '.join(result['fix_details'])}")
                        else:
                            print(f"  ✅ {filename}: No fixes needed")
                        results.append((filename, True, result['fixes_applied']))
                    else:
                        print(f"  ❌ {filename}: {result['error']}")
                        results.append((filename, False, 0))
                else:
                    print(f"  ⚠️  {filename}: File not found")
                    results.append((filename, False, 0))
        
        return {
            'total_files': sum(len(files) for files in key_platforms.values()),
            'files_fixed': self.files_fixed,
            'total_fixes': self.fixes_applied,
            'results': results
        }

def main():
    """Main fixing function"""
    print("=== MUTS PLATFORM AUTOMATIC FIXER ===\n")
    
    fixer = PlatformFixer()
    
    # Fix Priority 1 files
    priority_results = fixer.fix_priority_files()
    
    print(f"\n=== PRIORITY 1 RESULTS ===")
    print(f"Files processed: {priority_results['total_files']}")
    print(f"Files fixed: {priority_results['files_fixed']}")
    print(f"Total fixes applied: {priority_results['total_fixes']}")
    
    # Fix key platforms
    key_results = fixer.fix_key_platforms()
    
    print(f"\n=== KEY PLATFORMS RESULTS ===")
    print(f"Files processed: {key_results['total_files']}")
    print(f"Files fixed: {key_results['files_fixed']}")
    print(f"Total fixes applied: {key_results['total_fixes']}")
    
    # Test some fixed files
    print(f"\n=== TESTING FIXED FILES ===")
    
    test_files = ['versa2.py', 'cobb1.py', 'mds1.py', 'add13.py']
    
    for filename in test_files:
        if Path(filename).exists():
            try:
                spec = __import__('importlib.util').util.spec_from_file_location(filename.replace('.py', ''), filename)
                if spec:
                    module = __import__('importlib.util').util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    print(f"✅ {filename}: Import successful")
                else:
                    print(f"❌ {filename}: Could not create spec")
            except Exception as e:
                print(f"❌ {filename}: {e}")
    
    print(f"\n=== SUMMARY ===")
    print(f"Total files processed: {priority_results['total_files'] + key_results['total_files']}")
    print(f"Total fixes applied: {fixer.fixes_applied}")
    print(f"Files successfully fixed: {fixer.files_fixed}")
    
    if fixer.files_fixed > 0:
        print(f"\n🎉 SUCCESS: Fixed {fixer.files_fixed} platform files!")
        print(f"Run 'python3 test_platform_imports.py' to verify improvements.")
    else:
        print(f"\n⚠️  No files required fixing.")
    
    return fixer.files_fixed > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
