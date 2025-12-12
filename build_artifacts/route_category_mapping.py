#!/usr/bin/env python3
"""
Map existing backend routes to analysis artifact feature categories
"""
import json
import os

# Load gap report
with open('/home/lin/Desktop/sd-card/MUTS/build_artifacts/feature_gap_report.json', 'r') as f:
    gap_report = json.load(f)

# Existing backend routes
existing_routes = gap_report['existing_backend']['routes']

# Map routes to feature categories
route_mapping = {
    'ecu': ['can_communication', 'hardware_interfaces'],
    'diagnostics': ['diagnostic_services'],
    'tuning': ['tuning_maps', 'real_time_tuning'],
    'security': ['security_access'],
    'flash': ['rom_operations', 'checksum_calculation'],
    'logs': ['data_logging'],
    'torque-advisory': ['tuning_maps'],  # Part of tuning
    'swas': ['tuning_maps'],  # Part of tuning system
    'agents': ['gui_frameworks']  # UI orchestration
}

# Analyze coverage
print("Route to Feature Category Mapping:")
print("=" * 50)

all_categories = set(gap_report['master_features']['categories'].keys())
covered_categories = set()
for route, categories in route_mapping.items():
    if route in existing_routes:
        print(f"\n✅ {route}.ts -> covers: {', '.join(categories)}")
        covered_categories.update(categories)
    else:
        print(f"\n❌ {route}.ts -> MISSING (covers: {', '.join(categories)})")

# Find truly missing categories
truly_missing = all_categories - covered_categories
if truly_missing:
    print(f"\n⚠️  Truly Missing Categories: {truly_missing}")
else:
    print(f"\n✅ All feature categories are covered by existing routes!")

# Check special features that need attention
print(f"\nSpecial Security Features:")
print("- EEPROM unlock/backdoor features should be implemented in security.ts")
print("- These are NOT blocked per the new directive")

# Implementation plan
print(f"\nImplementation Plan:")
print("1. Extend existing routes with missing features from their categories")
print("2. Add security access methods (unlock, backdoor) to security.ts")
print("3. Ensure all 508 features are represented in the 9 existing routes")

# Save mapping
with open('/home/lin/Desktop/sd-card/MUTS/build_artifacts/route_category_mapping.json', 'w') as f:
    json.dump({
        'route_mapping': route_mapping,
        'covered_categories': list(covered_categories),
        'truly_missing': list(truly_missing),
        'implementation_plan': "Extend existing 9 routes to cover all features"
    }, f, indent=2)

print("\nMapping saved to: build_artifacts/route_category_mapping.json")
