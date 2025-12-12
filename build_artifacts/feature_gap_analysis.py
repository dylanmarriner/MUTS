#!/usr/bin/env python3
"""
Analyze feature gaps between master registry and existing backend
"""
import json
import os

# Load master feature registry
with open('/home/lin/Desktop/sd-card/MUTS/analysis_artifacts/master_feature_registry.json', 'r') as f:
    master_registry = json.load(f)

# Load component map
with open('/home/lin/Desktop/sd-card/MUTS/analysis_artifacts/component_map.json', 'r') as f:
    component_map = json.load(f)

# Extract all unique features from master registry
all_features = set()
feature_categories = {}

for category, data in master_registry['feature_categories'].items():
    feature_categories[category] = []
    for impl in data.get('implementations', []):
        feature = f"{impl['file']}:{impl['implementation']['type']}"
        all_features.add(feature)
        content = impl['implementation'].get('content', '')[:100]
        feature_categories[category].append({
            'file': impl['file'],
            'type': impl['implementation']['type'],
            'content': content
        })

# Check existing backend routes
backend_routes = set()
routes_dir = '/home/lin/Desktop/sd-card/MUTS/backend/src/routes'
if os.path.exists(routes_dir):
    for route_file in os.listdir(routes_dir):
        if route_file.endswith('.ts'):
            route_name = route_file.replace('.ts', '')
            backend_routes.add(route_name)

# Check existing Prisma models
prisma_models = set()
schema_file = '/home/lin/Desktop/sd-card/MUTS/backend/prisma/schema.prisma'
if os.path.exists(schema_file):
    with open(schema_file, 'r') as f:
        content = f.read()
        for line in content.split('\n'):
            if line.strip().startswith('model '):
                model_name = line.strip().split()[1]
                prisma_models.add(model_name)

# Analyze gaps
print(f"Master Registry Analysis:")
print(f"  Total feature categories: {len(feature_categories)}")
print(f"  Total unique features: {len(all_features)}")

print(f"\nFeature Categories:")
for category, features in feature_categories.items():
    print(f"  {category}: {len(features)} features")

print(f"\nExisting Backend:")
print(f"  Routes: {len(backend_routes)}")
print(f"  Models: {len(prisma_models)}")

# Identify missing features
missing_categories = set(feature_categories.keys()) - backend_routes
if missing_categories:
    print(f"\nMissing Route Categories: {missing_categories}")

# Check for special features that need implementation
special_features = []
for category, features in feature_categories.items():
    if category == 'security_access':
        for feature in features:
            if 'unlock' in feature['content'].lower() or 'backdoor' in feature['content'].lower():
                special_features.append(feature)

if special_features:
    print(f"\nSpecial Security Features to Implement:")
    for f in special_features[:5]:
        print(f"  - {f['file']}: {f['content']}")

# Save gap analysis
gap_report = {
    'master_features': {
        'total_categories': len(feature_categories),
        'total_features': len(all_features),
        'categories': {k: len(v) for k, v in feature_categories.items()}
    },
    'existing_backend': {
        'routes': list(backend_routes),
        'models': list(prisma_models)
    },
    'gaps': {
        'missing_routes': list(missing_categories),
        'special_features': special_features
    }
}

with open('/home/lin/Desktop/sd-card/MUTS/build_artifacts/feature_gap_report.json', 'w') as f:
    json.dump(gap_report, f, indent=2)

print("\nGap report saved to: build_artifacts/feature_gap_report.json")
