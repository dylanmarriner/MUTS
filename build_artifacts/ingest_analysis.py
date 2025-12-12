#!/usr/bin/env python3
"""
Ingest all analysis artifacts with hash pinning
"""
import os
import json
from datetime import datetime

# Load the hash manifest to get file hashes
with open('/home/lin/Desktop/sd-card/MUTS/build_artifacts/analysis_artifacts_hash_manifest.json', 'r') as f:
    manifest = json.load(f)

# Create a hash lookup
hash_lookup = {item['path']: item['sha256'] for item in manifest['files']}

# Initialize ingest index
ingest_index = {
    'metadata': {
        'total_files': len(manifest['files']),
        'ingestion_timestamp': datetime.now().timestamp(),
        'hash_verification': 'PINNED'
    },
    'files': {}
}

# Process each file
for file_info in manifest['files']:
    filepath = file_info['path']
    full_path = os.path.join('/home/lin/Desktop/sd-card/MUTS', filepath)
    
    print(f'Processing: {filepath}')
    
    # Read file content
    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Basic file analysis
    file_data = {
        'hash': file_info['sha256'],
        'size_bytes': file_info['size_bytes'],
        'mtime': file_info['mtime'],
        'content_length': len(content),
        'line_count': content.count('\n') + 1 if content else 0
    }
    
    # JSON-specific analysis
    if filepath.endswith('.json'):
        try:
            parsed = json.loads(content)
            if isinstance(parsed, list):
                file_data.update({
                    'type': 'json_array',
                    'length': len(parsed),
                    'item_types': list(set(type(item).__name__ for item in parsed[:10]))
                })
            elif isinstance(parsed, dict):
                file_data.update({
                    'type': 'json_object',
                    'keys': list(parsed.keys())[:10],
                    'key_count': len(parsed.keys()),
                    'has_nested_objects': any(isinstance(v, dict) for v in parsed.values()),
                    'has_arrays': any(isinstance(v, list) for v in parsed.values())
                })
        except Exception:
            file_data['type'] = 'invalid_json'
    
    # Python-specific analysis
    elif filepath.endswith('.py'):
        file_data.update({
            'type': 'python_script',
            'line_count': content.count('\n') + 1,
            'has_classes': 'class ' in content,
            'has_functions': 'def ' in content,
            'has_imports': 'import ' in content
        })
    
    # JSONL-specific analysis
    elif filepath.endswith('.jsonl'):
        lines = content.strip().split('\n')
        valid_json = 0
        for line in lines[:10]:  # Check first 10 lines
            try:
                json.loads(line)
                valid_json += 1
            except json.JSONDecodeError:
                pass
        file_data.update({
            'type': 'jsonl',
            'total_lines': len(lines),
            'valid_json_lines': valid_json
        })
    
    # Markdown analysis
    elif filepath.endswith('.md'):
        file_data.update({
            'type': 'markdown',
            'line_count': content.count('\n') + 1,
            'has_headers': '#' in content,
            'has_code_blocks': '```' in content
        })
    
    ingest_index['files'][filepath] = file_data

# Write ingest index
with open('/home/lin/Desktop/sd-card/MUTS/build_artifacts/analysis_ingest_index.json', 'w') as f:
    json.dump(ingest_index, f, indent=2)

print(f'\nIngested {len(ingest_index["files"])} files with hash pinning')
print('Written to: build_artifacts/analysis_ingest_index.json')
