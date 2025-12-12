#!/usr/bin/env python3
"""
Update normalized_features.json with hash citations
"""
import json

# Load existing normalized features
with open('/home/lin/Desktop/sd-card/MUTS/build_artifacts/normalized_features.json', 'r') as f:
    normalized = json.load(f)

# Load hash manifest
with open('/home/lin/Desktop/sd-card/MUTS/build_artifacts/analysis_artifacts_hash_manifest.json', 'r') as f:
    manifest = json.load(f)

# Create hash lookup
hash_lookup = {item['path']: item['sha256'] for item in manifest['files']}

# Update metadata
normalized['metadata']['hash_verification'] = 'ENABLED'
normalized['metadata']['hash_manifest_timestamp'] = manifest['generated_at']

# Add hash citations to each file entry
for category in normalized['normalized_features'].values():
    if 'files' in category:
        for file_entry in category['files']:
            # Map analysis file to actual file path
            analysis_file = f"analysis_artifacts/{file_entry['group']}_features.json"
            if analysis_file in hash_lookup:
                file_entry['source_hash'] = hash_lookup[analysis_file]
            else:
                # Try direct path
                if file_entry['file'] in hash_lookup:
                    file_entry['source_hash'] = hash_lookup[file_entry['file']]
                else:
                    file_entry['source_hash'] = 'NOT_FOUND'

# Add blocked features with hashes
if 'blocked_features' not in normalized:
    normalized['blocked_features'] = []

# Load conflicts for blocked features
with open('/home/lin/Desktop/sd-card/MUTS/build_artifacts/blocked_conflicts.json', 'r') as f:
    conflicts = json.load(f)

# Add security conflicts as blocked features
for vuln in conflicts['security_conflicts']['vulnerabilities']:
    normalized['blocked_features'].append({
        'feature': vuln['file'],
        'reason': vuln['issue'],
        'severity': vuln['severity'],
        'cwe': vuln['cwe'],
        'source_hash': hash_lookup.get(f'analysis_artifacts/{vuln["file"]}', 'NOT_FOUND')
    })

# Save updated normalized features
with open('/home/lin/Desktop/sd-card/MUTS/build_artifacts/normalized_features.json', 'w') as f:
    json.dump(normalized, f, indent=2)

print('Updated normalized_features.json with hash citations')
print(f'Total categories: {len(normalized["normalized_features"])}')
print(f'Blocked features: {len(normalized["blocked_features"])}')
