#!/usr/bin/env python3
"""
File enumeration script for MUTS forensic audit
Creates a comprehensive file manifest with all required metadata
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any

def get_file_info(file_path: Path, base_path: Path) -> Dict[str, Any]:
    """Get comprehensive file information"""
    try:
        stat = file_path.stat()
        
        # Determine file type
        if file_path.suffix.lower() in ['.py', '.pyw']:
            file_type = 'python'
        elif file_path.suffix.lower() in ['.md', '.txt', '.rst']:
            file_type = 'text'
        elif file_path.suffix.lower() in ['.json', '.yml', '.yaml']:
            file_type = 'data'
        elif file_path.suffix.lower() in ['.pdf', '.png', '.jpg', '.jpeg', '.gif']:
            file_type = 'binary'
        elif file_path.suffix.lower() in ['.pyc', '.pyo', '.pyd']:
            file_type = 'bytecode'
        else:
            file_type = 'other'
        
        # Check if file is readable and count lines
        readable = True
        line_count = 0
        parse_errors = []
        
        try:
            if file_type in ['python', 'text', 'data']:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    line_count = sum(1 for _ in f)
            elif file_type == 'binary':
                line_count = 0
                readable = False
        except Exception as e:
            readable = False
            parse_errors = [str(e)]
            line_count = 0
        
        return {
            "file_path": str(file_path.relative_to(base_path)),
            "file_type": file_type,
            "line_count": line_count,
            "size_bytes": stat.st_size,
            "readable": readable,
            "parse_errors": parse_errors
        }
    except Exception as e:
        return {
            "file_path": str(file_path.relative_to(base_path)),
            "file_type": "error",
            "line_count": 0,
            "size_bytes": 0,
            "readable": False,
            "parse_errors": [str(e)]
        }

def enumerate_files(base_path: Path) -> List[Dict[str, Any]]:
    """Recursively enumerate all files"""
    files = []
    
    for root, dirs, filenames in os.walk(base_path):
        # Skip hidden directories and common ignore patterns
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'venv', 'env']]
        
        for filename in filenames:
            # Skip hidden files
            if filename.startswith('.'):
                continue
                
            file_path = Path(root) / filename
            file_info = get_file_info(file_path, base_path)
            files.append(file_info)
    
    return files

def main():
    """Main function"""
    base_path = Path("/home/lin/Desktop/sd-card/MUTS")
    output_dir = base_path / "analysis_artifacts"
    output_dir.mkdir(exist_ok=True)
    
    print("Enumerating all files in MUTS repository...")
    files = enumerate_files(base_path)
    
    # Sort files by path for consistency
    files.sort(key=lambda x: x["file_path"])
    
    # Create manifest
    manifest = {
        "total_files": len(files),
        "enumeration_timestamp": "2025-12-12T23:40:00Z",
        "files": files
    }
    
    # Save manifest
    manifest_path = output_dir / "file_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"File manifest created: {manifest_path}")
    print(f"Total files enumerated: {len(files)}")
    
    # Print summary
    file_types = {}
    total_size = 0
    total_lines = 0
    
    for file_info in files:
        file_type = file_info["file_type"]
        file_types[file_type] = file_types.get(file_type, 0) + 1
        total_size += file_info["size_bytes"]
        total_lines += file_info["line_count"]
    
    print(f"\nSummary by file type:")
    for file_type, count in sorted(file_types.items()):
        print(f"  {file_type}: {count} files")
    print(f"\nTotal size: {total_size:,} bytes")
    print(f"Total lines: {total_lines:,}")

if __name__ == "__main__":
    main()