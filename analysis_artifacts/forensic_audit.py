#!/usr/bin/env python3
"""
Forensic audit script for MUTS repository
Performs line-by-line analysis of all files with group tagging
"""

import os
import json
import ast
import re
from pathlib import Path
from typing import Dict, List, Any, Set
from datetime import datetime

class ForensicAuditor:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.output_dir = base_path / "analysis_artifacts"
        self.output_dir.mkdir(exist_ok=True)
        
        # Output files
        self.per_file_analysis_path = self.output_dir / "per_file_analysis.jsonl"
        self.progress_path = self.output_dir / "progress.json"
        
        # Group checkpoint files
        self.group_files = {
            'ads': self.output_dir / "ads_features.json",
            'cobb': self.output_dir / "cobb_features.json",
            'mpsrom': self.output_dir / "mpsrom_features.json",
            'muts': self.output_dir / "muts_features.json",
            'versa': self.output_dir / "versa_features.json",
            'mds': self.output_dir / "mds_features.json",
            'other': self.output_dir / "other_features.json"
        }
        
        # Initialize group data
        self.group_data = {group: [] for group in self.group_files.keys()}
        
        # Load progress
        self.progress = self.load_progress()
        
    def load_progress(self) -> Dict[str, Any]:
        """Load or initialize progress tracking"""
        if self.progress_path.exists():
            with open(self.progress_path, 'r') as f:
                return json.load(f)
        return {
            "processed_files": [],
            "current_file_index": 0,
            "total_files": 0,
            "start_time": None,
            "last_file_processed": None
        }
    
    def save_progress(self):
        """Save current progress"""
        with open(self.progress_path, 'w') as f:
            json.dump(self.progress, f, indent=2)
    
    def determine_group_tags(self, file_path: str) -> List[str]:
        """Determine group tags based on file path and content"""
        tags = []
        path_lower = file_path.lower()
        
        # Check filename patterns
        if any(path_lower.startswith(p) for p in ['add', 'ads']):
            tags.append('ads')
        if any(path_lower.startswith(p) for p in ['cobb']):
            tags.append('cobb')
        if any(path_lower.startswith(p) for p in ['mpsrom']):
            tags.append('mpsrom')
        if any(path_lower.startswith(p) for p in ['muts']):
            tags.append('muts')
        if any(path_lower.startswith(p) for p in ['versa']):
            tags.append('versa')
        if any(path_lower.startswith(p) for p in ['mds']):
            tags.append('mds')
        
        # Check directory patterns
        if 'tuning' in path_lower:
            tags.append('tuning')
        if 'security' in path_lower:
            tags.append('security')
        if 'diagnostic' in path_lower:
            tags.append('diagnostic')
        
        # Default to 'other' if no specific tags
        if not tags:
            tags.append('other')
            
        return tags
    
    def analyze_python_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze Python file for features, components, etc."""
        analysis = {
            "file_path": str(file_path.relative_to(self.base_path)),
            "lines_read": 0,
            "features_found": [],
            "components_found": [],
            "algorithms": [],
            "protocols": [],
            "hardware_assumptions": [],
            "security_logic": [],
            "dead_or_disabled_code": [],
            "risks": [],
            "group_tags": []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                lines = content.split('\n')
                analysis["lines_read"] = len(lines)
                
            # Parse AST for structure
            try:
                tree = ast.parse(content)
                self.extract_ast_info(tree, analysis)
            except:
                pass  # Continue with regex analysis if AST fails
            
            # Line-by-line analysis
            for i, line in enumerate(lines, 1):
                self.analyze_line(line, i, analysis)
                
            # Extract imports
            self.extract_imports(content, analysis)
            
        except Exception as e:
            analysis["parse_errors"] = [str(e)]
            
        return analysis
    
    def extract_ast_info(self, tree: ast.AST, analysis: Dict[str, Any]):
        """Extract information from AST"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                analysis["components_found"].append({
                    "type": "class",
                    "name": node.name,
                    "line": node.lineno
                })
            elif isinstance(node, ast.FunctionDef):
                analysis["features_found"].append({
                    "type": "function",
                    "name": node.name,
                    "line": node.lineno
                })
    
    def analyze_line(self, line: str, line_num: int, analysis: Dict[str, Any]):
        """Analyze individual line for patterns"""
        line_stripped = line.strip()
        
        # Skip empty lines and comments only
        if not line_stripped or line_stripped.startswith('#'):
            if 'TODO' in line_stripped or 'FIXME' in line_stripped:
                analysis["dead_or_disabled_code"].append({
                    "type": "todo",
                    "line": line_num,
                    "content": line_stripped
                })
            return
        
        # Security patterns
        security_patterns = [
            r'password', r'key', r'encrypt', r'decrypt', 
            r'seed', r'algorithm', r'hash', r'cipher',
            r'security_access', r'authenticate', r'authorization'
        ]
        
        for pattern in security_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                analysis["security_logic"].append({
                    "type": "security_pattern",
                    "line": line_num,
                    "pattern": pattern,
                    "content": line_stripped[:100]
                })
        
        # Protocol patterns
        protocol_patterns = [
            r'CAN', r'OBD', r'ISO-TP', r'UDS', r'J2534',
            r'KWP', r'K-Line', r'0x[0-9A-Fa-f]+', r'PID'
        ]
        
        for pattern in protocol_patterns:
            if re.search(pattern, line):
                analysis["protocols"].append({
                    "type": "protocol",
                    "line": line_num,
                    "protocol": pattern,
                    "content": line_stripped[:100]
                })
        
        # Algorithm patterns
        if re.search(r'def.*algorithm|def.*calculate|def.*derive', line):
            analysis["algorithms"].append({
                "type": "algorithm_function",
                "line": line_num,
                "content": line_stripped[:100]
            })
        
        # Hardware assumptions
        hardware_patterns = [
            r'ECU', r'TCM', r'BCM', r'ABS', r'SRS',
            r'immobilizer', r'CAN bus', r'vehicle'
        ]
        
        for pattern in hardware_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                analysis["hardware_assumptions"].append({
                    "type": "hardware",
                    "line": line_num,
                    "hardware": pattern,
                    "content": line_stripped[:100]
                })
        
        # Dead/disabled code
        if line_stripped.startswith('#') and any(word in line_stripped.lower() for word in ['disabled', 'old', 'deprecated', 'unused']):
            analysis["dead_or_disabled_code"].append({
                "type": "disabled_code",
                "line": line_num,
                "content": line_stripped
            })
        
        # Risk patterns
        risk_patterns = [
            r'eval\(', r'exec\(', r'subprocess', r'os\.system',
            r'shell=True', r'hardcoded', r'tempfile', r'mktemp'
        ]
        
        for pattern in risk_patterns:
            if re.search(pattern, line):
                analysis["risks"].append({
                    "type": "security_risk",
                    "line": line_num,
                    "risk": pattern,
                    "content": line_stripped[:100]
                })
    
    def extract_imports(self, content: str, analysis: Dict[str, Any]):
        """Extract import statements"""
        import_patterns = [
            r'from\s+(\S+)\s+import',
            r'import\s+(\S+)'
        ]
        
        for pattern in import_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                analysis["features_found"].append({
                    "type": "import",
                    "module": match,
                    "line": None
                })
    
    def analyze_text_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze text file"""
        analysis = {
            "file_path": str(file_path.relative_to(self.base_path)),
            "lines_read": 0,
            "features_found": [],
            "components_found": [],
            "algorithms": [],
            "protocols": [],
            "hardware_assumptions": [],
            "security_logic": [],
            "dead_or_disabled_code": [],
            "risks": [],
            "group_tags": []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
                analysis["lines_read"] = len(lines)
                
                # Look for structured data in text files
                content = '\n'.join(lines)
                
                # Check for URLs, emails, API keys
                if re.search(r'https?://', content):
                    analysis["features_found"].append({
                        "type": "url_found",
                        "count": len(re.findall(r'https?://', content))
                    })
                
                # Check for configuration values
                if re.search(r'[A-Z_]+=\S+', content):
                    analysis["features_found"].append({
                        "type": "configuration_values",
                        "count": len(re.findall(r'[A-Z_]+=\S+', content))
                    })
                    
        except Exception as e:
            analysis["parse_errors"] = [str(e)]
            
        return analysis
    
    def analyze_binary_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze binary file"""
        return {
            "file_path": str(file_path.relative_to(self.base_path)),
            "lines_read": 0,
            "features_found": [{"type": "binary_file", "note": "Binary content not analyzed"}],
            "components_found": [],
            "algorithms": [],
            "protocols": [],
            "hardware_assumptions": [],
            "security_logic": [],
            "dead_or_disabled_code": [],
            "risks": [{"type": "binary_risk", "note": "Binary files may contain executable code"}],
            "group_tags": []
        }
    
    def append_to_per_file_analysis(self, analysis: Dict[str, Any]):
        """Append analysis to JSONL file"""
        with open(self.per_file_analysis_path, 'a') as f:
            json.dump(analysis, f)
            f.write('\n')
    
    def update_group_files(self, analysis: Dict[str, Any]):
        """Update group checkpoint files"""
        for tag in analysis["group_tags"]:
            if tag in self.group_data:
                self.group_data[tag].append({
                    "file_path": analysis["file_path"],
                    "features_count": len(analysis["features_found"]),
                    "components_count": len(analysis["components_found"]),
                    "algorithms_count": len(analysis["algorithms"]),
                    "risks_count": len(analysis["risks"])
                })
                
                # Save group file
                with open(self.group_files[tag], 'w') as f:
                    json.dump(self.group_data[tag], f, indent=2)
    
    def process_files(self):
        """Process all files from manifest"""
        # Load manifest
        manifest_path = self.output_dir / "file_manifest.json"
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        files = manifest["files"]
        self.progress["total_files"] = len(files)
        
        if not self.progress["start_time"]:
            self.progress["start_time"] = datetime.now().isoformat()
        
        # Start from where we left off
        start_index = 0
        if self.progress["processed_files"]:
            last_processed = self.progress["processed_files"][-1]
            for i, file_info in enumerate(files):
                if file_info["file_path"] == last_processed:
                    start_index = i + 1
                    break
        
        print(f"Starting forensic audit from file {start_index + 1} of {len(files)}")
        
        # Process each file
        for i in range(start_index, len(files)):
            file_info = files[i]
            file_path = self.base_path / file_info["file_path"]
            
            print(f"Processing file {i + 1}/{len(files)}: {file_info['file_path']}")
            
            # Determine group tags
            group_tags = self.determine_group_tags(file_info["file_path"])
            
            # Analyze based on file type
            if file_info["file_type"] == "python" and file_info["readable"]:
                analysis = self.analyze_python_file(file_path)
            elif file_info["file_type"] in ["text", "data"] and file_info["readable"]:
                analysis = self.analyze_text_file(file_path)
            else:
                analysis = self.analyze_binary_file(file_path)
            
            analysis["group_tags"] = group_tags
            
            # Save analysis immediately
            self.append_to_per_file_analysis(analysis)
            self.update_group_files(analysis)
            
            # Update progress
            self.progress["processed_files"].append(file_info["file_path"])
            self.progress["current_file_index"] = i
            self.progress["last_file_processed"] = file_info["file_path"]
            self.save_progress()
            
            # Print progress every 50 files
            if (i + 1) % 50 == 0:
                print(f"Progress: {i + 1}/{len(files)} files processed")
        
        print(f"\nForensic audit complete! Processed {len(files)} files.")
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate final summary"""
        summary = {
            "audit_complete": True,
            "total_files_processed": len(self.progress["processed_files"]),
            "completion_time": datetime.now().isoformat(),
            "group_statistics": {}
        }
        
        for group, data in self.group_data.items():
            summary["group_statistics"][group] = {
                "file_count": len(data),
                "total_features": sum(item["features_count"] for item in data),
                "total_components": sum(item["components_count"] for item in data),
                "total_algorithms": sum(item["algorithms_count"] for item in data),
                "total_risks": sum(item["risks_count"] for item in data)
            }
        
        # Save summary
        summary_path = self.output_dir / "audit_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\nAudit summary saved to: {summary_path}")
        
        # Print group statistics
        print("\nGroup Statistics:")
        for group, stats in summary["group_statistics"].items():
            print(f"  {group}: {stats['file_count']} files, "
                  f"{stats['total_features']} features, "
                  f"{stats['total_risks']} risks")

if __name__ == "__main__":
    base_path = Path("/home/lin/Desktop/sd-card/MUTS")
    auditor = ForensicAuditor(base_path)
    auditor.process_files()
