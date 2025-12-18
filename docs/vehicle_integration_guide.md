# Vehicle Integration Implementation Guide

## Overview
This document describes the complete implementation of full, end-to-end support for two real vehicles in the MUTS platform:
- Holden Commodore VF Evoke Wagon V6 3.0 Petrol 6AT (2015)
- Volkswagen Golf Mk6 TSI 90kW 1.4 Petrol 7DSG (2011)

## Architecture

### Database Models

#### VehicleProfile (`/app/muts/models/vehicle_profile.py`)
```python
class VehicleProfile(db.Model):
    vin = db.Column(db.String(17), db.ForeignKey('vehicles.id'), unique=True)
    plate = db.Column(db.String(20), nullable=False)
    engine_number = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    make = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    submodel = db.Column(db.String(100), nullable=False)
    body = db.Column(db.String(50), nullable=False)
    # ... additional fields
```

Key relationships:
- `vehicle` - Links to base Vehicle table (VIN as PK)
- `constants_preset` - Links to OEM constants
- `constants_versions` - One-to-many with VehicleConstants

### OEM Constants

#### Holden Commodore VF
- Vehicle Mass: 1780 kg (OEM spec)
- Drivetrain: RWD
- Transmission: 6-speed torque converter
- Gear Ratios: [4.58, 2.86, 1.88, 1.35, 1.00, 0.74]
- Final Drive: 2.92

#### VW Golf Mk6
- Vehicle Mass: 1295 kg (OEM spec)
- Drivetrain: FWD
- Transmission: 7-speed DSG
- Gear Ratios: [3.76, 2.27, 1.52, 1.13, 0.92, 0.81, 0.69]
- Final Drive: 3.16

### Diagnostics Templates

#### Holden VF Template
```python
commodore_vf = DiagnosticsCapabilityTemplate(
    manufacturer="Holden",
    platform="Zeta",
    model="Commodore",
    generation="VF",
    year_range=(2013, 2017)
)
```
Supported modules:
- Engine: SUPPORTED (E39A ECU)
- TCM: SUPPORTED (6L80)
- ABS: SUPPORTED (Bosch 9.0)
- SRS: SUPPORTED
- BCM: SUPPORTED
- Cluster: UNKNOWN (limited support)

#### VW Golf Mk6 Template
```python
golf_mk6 = DiagnosticsCapabilityTemplate(
    manufacturer="Volkswagen",
    platform="A6",
    model="Golf",
    generation="Mk6",
    year_range=(2010, 2013)
)
```
Supported modules:
- Engine: SUPPORTED (MED17)
- TCM: SUPPORTED (DQ200 DSG)
- ABS: SUPPORTED (ESP MK60)
- SRS: SUPPORTED
- BCM: SUPPORTED
- Cluster: NOT_SUPPORTED

## UI Implementation

### Hybrid Vehicle Selector

The vehicle selector provides two modes:
1. **Browse All** - Hierarchical navigation (Manufacturer → Model → Generation → Variant)
2. **My Vehicles** - Direct selection of saved VIN profiles

Key features:
- Tab-based mode switching
- Vehicle profile cards with VIN, plate, and details
- Add/Edit/Delete vehicle profiles
- Selected vehicle persistence

### API Endpoints

```
GET  /api/vehicles/my-vehicles          - Get user's saved profiles
POST /api/vehicles/profile               - Create new profile
DELETE /api/vehicles/profile/<vin>       - Delete profile
GET  /api/vehicles/manufacturers         - Browse manufacturers
GET  /api/vehicles/models                - Get models for manufacturer
GET  /api/vehicles/generations           - Get generations
GET  /api/vehicles/variants              - Get variants
GET  /api/vehicles/variant/<id>          - Get variant details
GET  /api/vehicles/profile/<vin>/constants - Get vehicle constants
```

## Special Features

### DSG Shift Detection (VW Golf)
- Implemented in `/app/muts/dyno/dsg_shift_detector.py`
- Monitors effective gear ratio changes
- Configured for 7-speed DSG ratios
- Guard windows to prevent false positives
- Integration with DynoRun for shift event storage

### RWD Configuration (Holden VF)
- Drivetrain type set to RWD in constants
- No AWD torque split parameters
- Proper final drive ratio for RWD

## Setup Instructions

### 1. Database Migration
```bash
flask db upgrade
```

### 2. Seed OEM Data
```bash
flask shell < app/muts/data/seed_oem_constants_flask.py
```

### 3. Run Setup Script
```bash
python app/muts/setup/vehicle_setup_complete.py
```

### 4. Verify Implementation
```bash
python app/muts/tests/vehicle_smoke_test.py
python app/muts/tests/test_dsg_detection.py
```

## Testing

### Smoke Tests (`/app/muts/tests/vehicle_smoke_test.py`)
Validates:
- Database models and relationships
- VIN profiles exist with correct data
- OEM constants properly configured
- Capability templates resolve correctly
- DSG detection available for VW
- RWD configured for Holden
- Vehicle switching isolation
- Dyno integration

### DSG Detection Test (`/app/muts/tests/test_dsg_detection.py`)
Validates:
- DSG detector initialization
- Shift detection with 7-speed ratios
- Dyno integration for shift events

## Key Design Decisions

1. **No Mock Data**: All specifications from OEM documentation
2. **Conservative Templates**: UNKNOWN = NOT_SUPPORTED for safety
3. **VIN as Primary Key**: Uses existing Vehicle table with VIN PK
4. **Hybrid UI**: Preserves browsing while adding direct access
5. **Versioned Constants**: Audit trail for all modifications
6. **Explicit Blocking**: UI shows "Not supported" clearly

## File Structure

```
/app/muts/
├── models/
│   ├── vehicle_profile.py              # VehicleProfile model
│   ├── diagnostics_registry.py         # Updated with Holden/VW
│   └── database_models.py              # Fixed VIN foreign key
├── data/
│   └── seed_oem_constants_flask.py     # OEM data seeder
├── api/
│   └── vehicles.py                     # Vehicle API endpoints
├── tests/
│   ├── vehicle_smoke_test.py           # Integration tests
│   └── test_dsg_detection.py           # DSG validation
├── setup/
│   └── vehicle_setup_complete.py       # Setup script
└── migrations/
    └── versions/
        └── 001_add_vehicle_profiles.py  # DB migration

/electron-app/
├── vehicle_selector.html               # UI component
├── vehicle_selector.js                 # UI logic
└── styles.css                          # Added vehicle selector styles
```

## Future Enhancements

1. **Additional Vehicles**: Follow same pattern for new makes/models
2. **VIN Auto-detection**: Lookup vehicle specs from VIN
3. **Constants Import**: CSV/JSON import for custom vehicles
4. **Template Editor**: UI for modifying capability templates
5. **Advanced DSG**: Support for more DSG variants

## Troubleshooting

### Common Issues

1. **Migration Fails**: Ensure Flask app context is properly initialized
2. **VIN Not Found**: Check VehicleProfile table exists and has data
3. **Templates Missing**: Verify diagnostics_registry.py imports correctly
4. **DSG Detection**: Confirm transmission type is set to DSG in constants

### Debug Commands

```python
# Check vehicle profiles
from muts.models.vehicle_profile import VehicleProfile
VehicleProfile.query.all()

# Verify constants
from muts.models.vehicle_constants import VehicleConstantsPreset
VehicleConstantsPreset.query.filter_by(manufacturer='Volkswagen').first()

# Test templates
from muts.models.diagnostics_registry import template_registry
template_registry.find_template('Volkswagen', 'Golf', 2011, 'A6')
```

## Conclusion

This implementation provides complete, first-class support for the Holden Commodore VF and VW Golf Mk6 vehicles with full integration across all MUTS platform components. The architecture is extensible and can accommodate additional vehicles following the established patterns.
