#!/usr/bin/env python3
"""
Drift detection for analysis artifacts
"""
import os
import json
import hashlib
from datetime import datetime

def compute_sha256(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

# Load original manifest
with open('/home/lin/Desktop/sd-card/MUTS/build_artifacts/analysis_artifacts_hash_manifest.json', 'r') as f:
    original_manifest = json.load(f)

# Create hash lookup from original
original_hashes = {item['path']: item['sha256'] for item in original_manifest['files']}

# Recompute current hashes
current_dir = '/home/lin/Desktop/sd-card/MUTS/analysis_artifacts'
current_files = {}
drift_report = {
    'generated_at': datetime.now().isoformat(),
    'drift_detected': False,
    'drift_details': []
}

# Enumerate current files
for root, dirs, filenames in os.walk(current_dir):
    for filename in filenames:
        filepath = os.path.join(root, filename)
        rel_path = os.path.relpath(filepath, '/home/lin/Desktop/sd-card/MUTS')
        
        current_hash = compute_sha256(filepath)
        current_files[rel_path] = current_hash
        
        # Check for modifications
        if rel_path in original_hashes:
            if original_hashes[rel_path] != current_hash:
                drift_report['drift_detected'] = True
                drift_report['drift_details'].append({
                    'file': rel_path,
                    'drift_type': 'modified',
                    'old_hash': original_hashes[rel_path],
                    'new_hash': current_hash
                })
        else:
            # New file
            drift_report['drift_detected'] = True
            drift_report['drift_details'].append({
                'file': rel_path,
                'drift_type': 'added',
                'old_hash': None,
                'new_hash': current_hash
            })

# Check for removed files
for original_path in original_hashes:
    if original_path not in current_files:
        drift_report['drift_detected'] = True
        drift_report['drift_details'].append({
            'file': original_path,
            'drift_type': 'removed',
            'old_hash': original_hashes[original_path],
            'new_hash': None
        })

# Write drift report
with open('/home/lin/Desktop/sd-card/MUTS/build_artifacts/analysis_drift_report.json', 'w') as f:
    json.dump(drift_report, f, indent=2)

if drift_report['drift_detected']:
    print(f'⚠️  DRIFT DETECTED!')
    print(f'   {len(drift_report["drift_details"])} files have changed')
    print('   Written to: build_artifacts/analysis_drift_report.json')
    print('\nDO NOT PROCEED until drift is resolved!')
else:
    print('✅ No drift detected - all hashes match')
    print('   Written to: build_artifacts/analysis_drift_report.json')
