"""MUTS FastAPI Service - Database API for Electron Frontend"""

from fastapi import FastAPI, HTTPException, Depends, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
import csv
import io
import sys
import os
from datetime import datetime

# Add parent directory to path to import MUTS modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from muts.models.database_models import (
    Vehicle, ECUData, DiagnosticTroubleCode, TuningProfile, LogEntry,
    PerformanceRun, FlashHistory, DynoRun, DynoSample, TelemetrySession,
    VehicleConstants, VehicleConstantsPreset, User, TransmissionType, DrivetrainType
)
from muts.models.database import get_db, engine
from muts.dyno.service import DynoService

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="MUTS Database API", version="0.1.0")

# Enable CORS for Electron
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to Electron app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency to get DB session
def get_db_session():
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()


# Helper function to convert model to dict
def model_to_dict(model) -> Dict[str, Any]:
    """Convert SQLAlchemy model to dictionary"""
    if hasattr(model, 'to_dict'):
        return model.to_dict()
    return {c.name: getattr(model, c.name) for c in model.__table__.columns}


# Validation models
class VehicleConstantsOverride(BaseModel):
    vehicle_mass: Optional[float] = None
    driver_fuel_estimate: Optional[float] = None
    drag_coefficient: Optional[float] = None
    frontal_area: Optional[float] = None
    rolling_resistance: Optional[float] = None
    air_density: Optional[float] = None
    wheel_radius: Optional[float] = None
    drivetrain_efficiency: Optional[float] = None
    road_grade: Optional[float] = None
    gravity: Optional[float] = None
    gear_ratios: Optional[List[float]] = None
    final_drive_ratio: Optional[float] = None
    
    @validator('vehicle_mass')
    def validate_vehicle_mass(cls, v):
        if v is not None and (v <= 0 or v > 10000):
            raise ValueError('Vehicle mass must be between 0 and 10000 kg')
        return v
    
    @validator('driver_fuel_estimate')
    def validate_driver_fuel(cls, v):
        if v is not None and (v < 0 or v > 500):
            raise ValueError('Driver + fuel estimate must be between 0 and 500 kg')
        return v
    
    @validator('drag_coefficient')
    def validate_drag_coefficient(cls, v):
        if v is not None and (v < 0.1 or v > 1.0):
            raise ValueError('Drag coefficient must be between 0.1 and 1.0')
        return v
    
    @validator('frontal_area')
    def validate_frontal_area(cls, v):
        if v is not None and (v <= 0 or v > 10):
            raise ValueError('Frontal area must be between 0 and 10 m²')
        return v
    
    @validator('rolling_resistance')
    def validate_rolling_resistance(cls, v):
        if v is not None and (v < 0.005 or v > 0.05):
            raise ValueError('Rolling resistance must be between 0.005 and 0.05')
        return v
    
    @validator('air_density')
    def validate_air_density(cls, v):
        if v is not None and (v <= 0 or v > 2):
            raise ValueError('Air density must be between 0 and 2 kg/m³')
        return v
    
    @validator('wheel_radius')
    def validate_wheel_radius(cls, v):
        if v is not None and (v <= 0 or v > 1):
            raise ValueError('Wheel radius must be between 0 and 1 m')
        return v
    
    @validator('drivetrain_efficiency')
    def validate_drivetrain_efficiency(cls, v):
        if v is not None and (v < 0.7 or v > 0.98):
            raise ValueError('Drivetrain efficiency must be between 0.7 and 0.98')
        return v
    
    @validator('road_grade')
    def validate_road_grade(cls, v):
        if v is not None and (v < -45 or v > 45):
            raise ValueError('Road grade must be between -45 and 45 degrees')
        return v
    
    @validator('gravity')
    def validate_gravity(cls, v):
        if v is not None and (v <= 0 or v > 20):
            raise ValueError('Gravity must be between 0 and 20 m/s²')
        return v
    
    @validator('gear_ratios')
    def validate_gear_ratios(cls, v):
        if v is not None:
            if len(v) != 6:
                raise ValueError('Must provide exactly 6 gear ratios')
            for ratio in v:
                if ratio <= 0 or ratio > 10:
                    raise ValueError('Each gear ratio must be between 0 and 10')
        return v
    
    @validator('final_drive_ratio')
    def validate_final_drive_ratio(cls, v):
        if v is not None and (v <= 0 or v > 10):
            raise ValueError('Final drive ratio must be between 0 and 10')
        return v


class VehicleConstantsCreate(BaseModel):
    preset_id: int
    note: Optional[str] = ""
    overrides: VehicleConstantsOverride

# Validation models for imports
class VehiclePresetImport(BaseModel):
    name: str
    manufacturer: str
    platform: Optional[str] = None
    model: str
    generation: Optional[str] = None
    variant: Optional[str] = None
    year: int
    chassis: Optional[str] = None
    engine: Optional[str] = None
    transmission_type: str
    drivetrain_type: str
    vehicle_mass: float
    driver_fuel_estimate: float = 95
    drag_coefficient: float
    frontal_area: float
    rolling_resistance: float
    air_density: float = 1.225
    wheel_radius: float
    drivetrain_efficiency: float
    manual_efficiency: Optional[float] = None
    auto_efficiency: Optional[float] = None
    road_grade: float = 0.0
    gravity: float = 9.80665
    gear_ratios: List[float]
    final_drive_ratio: float
    awd_torque_split_front: Optional[float] = 0.5
    awd_torque_split_rear: Optional[float] = 0.5
    source: Optional[str] = "Imported (User)"
    
    @validator('transmission_type')
    def validate_transmission(cls, v):
        valid_types = [t.value for t in TransmissionType]
        if v.upper() not in valid_types:
            raise ValueError(f'Invalid transmission type. Must be one of: {valid_types}')
        return v.upper()
    
    @validator('drivetrain_type')
    def validate_drivetrain(cls, v):
        valid_types = [t.value for t in DrivetrainType]
        if v.upper() not in valid_types:
            raise ValueError(f'Invalid drivetrain type. Must be one of: {valid_types}')
        return v.upper()
    
    @validator('gear_ratios')
    def validate_gear_ratios(cls, v):
        if len(v) < 5 or len(v) > 8:
            raise ValueError('Must provide 5-8 gear ratios')
        for ratio in v:
            if ratio <= 0 or ratio > 20:
                raise ValueError('Each gear ratio must be between 0 and 20')
        return v
    
    @validator('vehicle_mass')
    def validate_mass(cls, v):
        if v <= 0 or v > 10000:
            raise ValueError('Vehicle mass must be between 0 and 10000 kg')
        return v
    
    @validator('drag_coefficient')
    def validate_drag(cls, v):
        if v < 0.1 or v > 1.0:
            raise ValueError('Drag coefficient must be between 0.1 and 1.0')
        return v
    
    @validator('frontal_area')
    def validate_frontal(cls, v):
        if v <= 0 or v > 10:
            raise ValueError('Frontal area must be between 0 and 10 m²')
        return v
    
    @validator('rolling_resistance')
    def validate_rolling(cls, v):
        if v < 0.005 or v > 0.05:
            raise ValueError('Rolling resistance must be between 0.005 and 0.05')
        return v
    
    @validator('drivetrain_efficiency')
    def validate_efficiency(cls, v):
        if v < 0.7 or v > 0.98:
            raise ValueError('Drivetrain efficiency must be between 0.7 and 0.98')
        return v

class ImportValidationResult(BaseModel):
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    preset: Optional[VehiclePresetImport] = None

# ===== VEHICLE ENDPOINTS =====
@app.get("/api/vehicles", response_model=List[Dict[str, Any]])
async def get_vehicles(db: Session = Depends(get_db_session)):
    """Get all vehicles"""
    vehicles = db.query(Vehicle).all()
    return [model_to_dict(v) for v in vehicles]


@app.post("/api/vehicles", response_model=Dict[str, Any])
async def create_vehicle(vehicle_data: Dict[str, Any], db: Session = Depends(get_db_session)):
    """Create a new vehicle"""
    vehicle = Vehicle(**vehicle_data)
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return model_to_dict(vehicle)


@app.delete("/api/vehicles/{vehicle_id}", response_model=Dict[str, bool])
async def delete_vehicle(vehicle_id: int, db: Session = Depends(get_db_session)):
    """Delete a vehicle"""
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    db.delete(vehicle)
    db.commit()
    return {"success": True}


# ===== DIAGNOSTIC TROUBLE CODES ENDPOINTS =====
@app.get("/api/dtc/{vehicle_id}", response_model=List[Dict[str, Any]])
async def get_dtcs(vehicle_id: int, db: Session = Depends(get_db_session)):
    """Get all DTCs for a vehicle"""
    dtcs = db.query(DiagnosticTroubleCode).filter(
        DiagnosticTroubleCode.vehicle_id == vehicle_id
    ).all()
    return [model_to_dict(dtc) for dtc in dtcs]


@app.post("/api/dtc/{vehicle_id}", response_model=Dict[str, Any])
async def create_dtc(vehicle_id: int, dtc_data: Dict[str, Any], db: Session = Depends(get_db_session)):
    """Create a new DTC"""
    dtc_data['vehicle_id'] = vehicle_id
    dtc = DiagnosticTroubleCode(**dtc_data)
    db.add(dtc)
    db.commit()
    db.refresh(dtc)
    return model_to_dict(dtc)


@app.delete("/api/dtc/{dtc_id}", response_model=Dict[str, bool])
async def clear_dtc(dtc_id: int, db: Session = Depends(get_db_session)):
    """Clear a DTC"""
    dtc = db.query(DiagnosticTroubleCode).filter(
        DiagnosticTroubleCode.id == dtc_id
    ).first()
    if not dtc:
        raise HTTPException(status_code=404, detail="DTC not found")
    db.delete(dtc)
    db.commit()
    return {"success": True}


# ===== LOG ENDPOINTS =====
@app.get("/api/logs", response_model=List[Dict[str, Any]])
async def get_logs(
    level: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db_session)
):
    """Get system logs with optional filtering"""
    query = db.query(LogEntry)
    if level and level != "all":
        query = query.filter(LogEntry.level == level.upper())
    logs = query.order_by(LogEntry.timestamp.desc()).limit(limit).all()
    return [model_to_dict(log) for log in logs]


@app.post("/api/logs", response_model=Dict[str, Any])
async def create_log(log_data: Dict[str, Any], db: Session = Depends(get_db_session)):
    """Create a new log entry"""
    if 'timestamp' not in log_data:
        log_data['timestamp'] = datetime.utcnow()
    log = LogEntry(**log_data)
    db.add(log)
    db.commit()
    db.refresh(log)
    return model_to_dict(log)


# ===== PERFORMANCE RUN ENDPOINTS =====
@app.get("/api/performance-runs/{vehicle_id}", response_model=List[Dict[str, Any]])
async def get_performance_runs(vehicle_id: int, db: Session = Depends(get_db_session)):
    """Get all performance runs for a vehicle"""
    runs = db.query(PerformanceRun).filter(
        PerformanceRun.vehicle_id == vehicle_id
    ).order_by(PerformanceRun.start_time.desc()).all()
    return [model_to_dict(run) for run in runs]


@app.post("/api/performance-runs/{vehicle_id}", response_model=Dict[str, Any])
async def create_performance_run(
    vehicle_id: int, 
    run_data: Dict[str, Any], 
    db: Session = Depends(get_db_session)
):
    """Create a new performance run"""
    run_data['vehicle_id'] = vehicle_id
    if 'start_time' not in run_data:
        run_data['start_time'] = datetime.utcnow()
    run = PerformanceRun(**run_data)
    db.add(run)
    db.commit()
    db.refresh(run)
    return model_to_dict(run)


# ===== SECURITY EVENT ENDPOINTS =====
@app.get("/api/security-events", response_model=List[Dict[str, Any]])
async def get_security_events(
    event_type: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db_session)
):
    """Get security events with optional filtering"""
    query = db.query(SecurityEvent)
    if event_type and event_type != "all":
        query = query.filter(SecurityEvent.event_type == event_type)
    events = query.order_by(SecurityEvent.timestamp.desc()).limit(limit).all()
    return [model_to_dict(event) for event in events]


@app.post("/api/security-events", response_model=Dict[str, Any])
async def create_security_event(event_data: Dict[str, Any], db: Session = Depends(get_db_session)):
    """Create a new security event"""
    if 'timestamp' not in event_data:
        event_data['timestamp'] = datetime.utcnow()
    event = SecurityEvent(**event_data)
    db.add(event)
    db.commit()
    db.refresh(event)
    return model_to_dict(event)


# ===== AI MODEL ENDPOINTS =====
@app.get("/api/ai-models", response_model=List[Dict[str, Any]])
async def get_ai_models(db: Session = Depends(get_db_session)):
    """Get all AI models"""
    models = db.query(AIModel).all()
    return [model_to_dict(model) for model in models]


@app.post("/api/ai-models", response_model=Dict[str, Any])
async def create_ai_model(model_data: Dict[str, Any], db: Session = Depends(get_db_session)):
    """Create a new AI model"""
    if 'created_at' not in model_data:
        model_data['created_at'] = datetime.utcnow()
    model = AIModel(**model_data)
    db.add(model)
    db.commit()
    db.refresh(model)
    return model_to_dict(model)


# ===== TRAINING DATA ENDPOINTS =====
@app.get("/api/training-data", response_model=List[Dict[str, Any]])
async def get_training_data(limit: int = 100, db: Session = Depends(get_db_session)):
    """Get training data"""
    data = db.query(TrainingData).order_by(
        TrainingData.created_at.desc()
    ).limit(limit).all()
    return [model_to_dict(d) for d in data]


@app.post("/api/training-data", response_model=Dict[str, Any])
async def create_training_data(data: Dict[str, Any], db: Session = Depends(get_db_session)):
    """Create new training data"""
    if 'created_at' not in data:
        data['created_at'] = datetime.utcnow()
    training_data = TrainingData(**data)
    db.add(training_data)
    db.commit()
    db.refresh(training_data)
    return model_to_dict(training_data)


# ===== TELEMETRY SESSION ENDPOINTS =====
@app.get("/api/telemetry-sessions/{vehicle_id}", response_model=List[Dict[str, Any]])
async def get_telemetry_sessions(vehicle_id: int, db: Session = Depends(get_db_session)):
    """Get all telemetry sessions for a vehicle"""
    sessions = db.query(TelemetrySession).filter(
        TelemetrySession.vehicle_id == vehicle_id
    ).order_by(TelemetrySession.start_time.desc()).all()
    return [model_to_dict(session) for session in sessions]


@app.post("/api/telemetry-sessions/{vehicle_id}", response_model=Dict[str, Any])
async def create_telemetry_session(
    vehicle_id: int,
    session_data: Dict[str, Any],
    db: Session = Depends(get_db_session)
):
    """Create a new telemetry session"""
    session_data['vehicle_id'] = vehicle_id
    if 'start_time' not in session_data:
        session_data['start_time'] = datetime.utcnow()
    session = TelemetrySession(**session_data)
    db.add(session)
    db.commit()
    db.refresh(session)
    return model_to_dict(session)


# ===== USER SESSION ENDPOINTS =====
@app.get("/api/current-user", response_model=Dict[str, Any])
async def get_current_user(db: Session = Depends(get_db_session)):
    """Get current user (for demo, returns first user)"""
    user = db.query(User).first()
    if not user:
        # Create default user if none exists
        user = User(
            username="guest",
            email="guest@muts.local",
            role="viewer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return model_to_dict(user)


@app.post("/api/login", response_model=Dict[str, Any])
async def login(credentials: Dict[str, str], db: Session = Depends(get_db_session)):
    """Login user"""
    # Simple demo login - check if user exists
    user = db.query(User).filter(
        User.username == credentials.get('username')
    ).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create session
    session = UserSession(
        user_id=user.id,
        login_time=datetime.utcnow(),
        active=True
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return {
        "user": model_to_dict(user),
        "session": model_to_dict(session)
    }


@app.post("/api/logout", response_model=Dict[str, bool])
async def logout(db: Session = Depends(get_db_session)):
    """Logout current user"""
    # Deactivate all active sessions
    db.query(UserSession).filter(UserSession.active == True).update(
        {"active": False, "logout_time": datetime.utcnow()}
    )
    db.commit()
    return {"success": True}


# ===== DYNO ENDPOINTS =====
@app.post("/api/dyno/runs", response_model=Dict[str, Any])
async def create_dyno_run(
    vehicle_id: str,
    telemetry_session_id: int,
    tuning_profile_id: Optional[int] = None,
    db: Session = Depends(get_db_session)
):
    """Create a new dyno run"""
    try:
        dyno_service = DynoService(db)
        dyno_run = dyno_service.create_dyno_run(
            vehicle_id=vehicle_id,
            telemetry_session_id=telemetry_session_id,
            tuning_profile_id=tuning_profile_id
        )
        return model_to_dict(dyno_run)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/dyno/runs/{run_id}/process", response_model=Dict[str, Any])
async def process_dyno_run(run_id: int, db: Session = Depends(get_db_session)):
    """Process a dyno run and calculate results"""
    try:
        dyno_service = DynoService(db)
        result = dyno_service.process_dyno_run(run_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dyno/runs", response_model=List[Dict[str, Any]])
async def get_dyno_runs(
    vehicle_id: Optional[str] = None,
    db: Session = Depends(get_db_session)
):
    """Get dyno runs for a vehicle or all runs"""
    try:
        dyno_service = DynoService(db)
        runs = dyno_service.get_dyno_runs(vehicle_id=vehicle_id)
        return runs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dyno/runs/{run_id}", response_model=Dict[str, Any])
async def get_dyno_run(run_id: int, db: Session = Depends(get_db_session)):
    """Get detailed dyno run with samples"""
    try:
        dyno_service = DynoService(db)
        run = dyno_service.get_dyno_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Dyno run not found")
        return run
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dyno/runs/{run1_id}/compare/{run2_id}", response_model=Dict[str, Any])
async def compare_dyno_runs(
    run1_id: int,
    run2_id: int,
    db: Session = Depends(get_db_session)
):
    """Compare two dyno runs (before/after tune)"""
    try:
        dyno_service = DynoService(db)
        comparison = dyno_service.compare_runs(run1_id, run2_id)
        return comparison
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dyno/runs/{run_id}/samples", response_model=List[Dict[str, Any]])
async def get_dyno_samples(run_id: int, db: Session = Depends(get_db_session)):
    """Get raw samples for a dyno run"""
    try:
        samples = db.query(DynoSample).filter(
            DynoSample.dyno_run_id == run_id
        ).order_by(DynoSample.timestamp).all()
        return [model_to_dict(s) for s in samples]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== HEALTH CHECK =====
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0"
    }

# Vehicle Constants endpoints
@app.get("/api/vehicles/constants/presets", response_model=List[dict])
async def get_constants_presets(db: Session = Depends(get_db_session)):
    """Get all available vehicle constants presets"""
    presets = db.query(VehicleConstantsPreset).all()
    return [p.to_dict() for p in presets]


@app.post("/api/vehicles/constants/import/validate", response_model=ImportValidationResult)
async def validate_import(file: bytes = File(...), format: str = Form(...)):
    """Validate a CSV or JSON import file without saving"""
    try:
        if format.lower() == 'csv':
            content = file.decode('utf-8')
            reader = csv.DictReader(io.StringIO(content))
            
            # Check required headers
            required_headers = [
                'name', 'manufacturer', 'model', 'year', 'transmission_type',
                'drivetrain_type', 'vehicle_mass', 'drag_coefficient',
                'frontal_area', 'rolling_resistance', 'wheel_radius',
                'drivetrain_efficiency', 'gear_ratios', 'final_drive_ratio'
            ]
            
            headers = reader.fieldnames or []
            missing_headers = [h for h in required_headers if h not in headers]
            
            if missing_headers:
                return ImportValidationResult(
                    valid=False,
                    errors=[f"Missing required columns: {', '.join(missing_headers)}"]
                )
            
            # Parse first row for validation
            row = next(reader, None)
            if not row:
                return ImportValidationResult(
                    valid=False,
                    errors=["File is empty"]
                )
            
            # Convert gear ratios from string to list
            try:
                gear_ratios = [float(x.strip()) for x in row['gear_ratios'].split(',')]
            except:
                return ImportValidationResult(
                    valid=False,
                    errors=["Invalid gear ratios format. Use comma-separated values."]
                )
            
            # Build preset data
            preset_data = {
                **row,
                'gear_ratios': gear_ratios,
                'year': int(row['year']),
                'vehicle_mass': float(row['vehicle_mass']),
                'drag_coefficient': float(row['drag_coefficient']),
                'frontal_area': float(row['frontal_area']),
                'rolling_resistance': float(row['rolling_resistance']),
                'wheel_radius': float(row['wheel_radius']),
                'drivetrain_efficiency': float(row['drivetrain_efficiency']),
                'final_drive_ratio': float(row['final_drive_ratio'])
            }
            
            # Handle optional fields
            for field in ['driver_fuel_estimate', 'air_density', 'road_grade', 'gravity']:
                if field in row and row[field]:
                    preset_data[field] = float(row[field])
            
        elif format.lower() == 'json':
            content = json.loads(file.decode('utf-8'))
            
            if isinstance(content, list):
                if not content:
                    return ImportValidationResult(
                        valid=False,
                        errors=["JSON file is empty"]
                    )
                preset_data = content[0]  # Validate first entry
            else:
                preset_data = content
            
        else:
            return ImportValidationResult(
                valid=False,
                errors=[f"Unsupported format: {format}. Use CSV or JSON."]
            )
        
        # Validate the preset
        try:
            preset = VehiclePresetImport(**preset_data)
            
            # Check for warnings
            warnings = []
            warnings.append("Imported profiles have reduced confidence score")
            
            if preset.drivetrain_type == 'AWD_HALDEX' and not (preset.awd_torque_split_front and preset.awd_torque_split_rear):
                warnings.append("AWD vehicles should specify torque split")
            
            return ImportValidationResult(
                valid=True,
                warnings=warnings,
                preset=preset
            )
            
        except ValueError as e:
            return ImportValidationResult(
                valid=False,
                errors=[str(e)]
            )
        except Exception as e:
            return ImportValidationResult(
                valid=False,
                errors=[f"Validation error: {str(e)}"]
            )
    
    except Exception as e:
        return ImportValidationResult(
            valid=False,
            errors=[f"File processing error: {str(e)}"]
        )


@app.post("/api/vehicles/constants/import", response_model=dict)
async def import_preset(file: bytes = File(...), format: str = Form(...), db: Session = Depends(get_db_session)):
    """Import and save a vehicle constants preset"""
    # First validate
    validation = await validate_import(file, format)
    
    if not validation.valid:
        raise HTTPException(status_code=400, detail=validation.errors)
    
    try:
        preset = validation.preset
        
        # Check if already exists
        existing = db.query(VehicleConstantsPreset).filter_by(
            manufacturer=preset.manufacturer,
            platform=preset.platform,
            model=preset.model,
            generation=preset.generation,
            variant=preset.variant,
            transmission_type=TransmissionType(preset.transmission_type)
        ).first()
        
        if existing:
            raise HTTPException(status_code=409, detail="A preset with these specifications already exists")
        
        # Create new preset
        new_preset = VehicleConstantsPreset(
            name=preset.name,
            manufacturer=preset.manufacturer,
            platform=preset.platform,
            model=preset.model,
            generation=preset.generation,
            variant=preset.variant,
            year=preset.year,
            chassis=preset.chassis,
            engine=preset.engine,
            transmission_type=TransmissionType(preset.transmission_type),
            drivetrain_type=DrivetrainType(preset.drivetrain_type),
            vehicle_mass=preset.vehicle_mass,
            driver_fuel_estimate=preset.driver_fuel_estimate,
            drag_coefficient=preset.drag_coefficient,
            frontal_area=preset.frontal_area,
            rolling_resistance=preset.rolling_resistance,
            air_density=preset.air_density,
            wheel_radius=preset.wheel_radius,
            drivetrain_efficiency=preset.drivetrain_efficiency,
            manual_efficiency=preset.manual_efficiency,
            auto_efficiency=preset.auto_efficiency,
            road_grade=preset.road_grade,
            gravity=preset.gravity,
            final_drive_ratio=preset.final_drive_ratio,
            awd_torque_split_front=preset.awd_torque_split_front,
            awd_torque_split_rear=preset.awd_torque_split_rear,
            source=preset.source,
            source_type="USER_IMPORT",
            confidence_score=95,  # Start high, deductions calculated dynamically
            created_by=1  # TODO: Get from auth
        )
        
        # Set gear ratios
        new_preset.set_gear_ratios(preset.gear_ratios)
        
        db.add(new_preset)
        db.commit()
        db.refresh(new_preset)
        
        return {
            "success": True,
            "preset": new_preset.to_dict(),
            "warnings": validation.warnings
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@app.get("/api/vehicles/constants/hierarchy", response_model=List[Dict[str, Any]])
async def get_preset_hierarchy(db: Session = Depends(get_db_session)):
    """Get all presets organized by manufacturer -> platform -> model -> variant"""
    presets = db.query(VehicleConstantsPreset).order_by(
        VehicleConstantsPreset.manufacturer,
        VehicleConstantsPreset.platform,
        VehicleConstantsPreset.model,
        VehicleConstantsPreset.year
    ).all()
    
    hierarchy = {}
    
    for preset in presets:
        manufacturer = preset.manufacturer
        if manufacturer not in hierarchy:
            hierarchy[manufacturer] = {}
        
        platform = preset.platform or "Unknown"
        if platform not in hierarchy[manufacturer]:
            hierarchy[manufacturer][platform] = {}
        
        model = preset.model
        if model not in hierarchy[manufacturer][platform]:
            hierarchy[manufacturer][platform][model] = []
        
        hierarchy[manufacturer][platform][model].append({
            'id': preset.id,
            'name': preset.name,
            'generation': preset.generation,
            'variant': preset.variant,
            'year': preset.year,
            'transmission_type': preset.transmission_type.value,
            'drivetrain_type': preset.drivetrain_type.value,
            'source_type': preset.source_type,
            'confidence_score': preset.confidence_score
        })
    
    return hierarchy

@app.get("/api/vehicles/{vehicle_id}/constants", response_model=List[dict])
async def get_vehicle_constants(vehicle_id: int, db: Session = Depends(get_db_session)):
    """Get all constants versions for a vehicle"""
    constants = db.query(VehicleConstants).filter_by(vehicle_id=vehicle_id).all()
    return [c.to_dict() for c in constants]

@app.get("/api/vehicles/{vehicle_id}/constants/active", response_model=dict)
async def get_active_vehicle_constants(vehicle_id: int, db: Session = Depends(get_db_session)):
    """Get the active constants for a vehicle"""
    constants = db.query(VehicleConstants).filter_by(
        vehicle_id=vehicle_id, is_active=True
    ).first()
    if not constants:
        raise HTTPException(status_code=404, detail="No active constants found")
    return constants.to_dict()

@app.post("/api/vehicles/{vehicle_id}/constants", response_model=dict)
async def create_vehicle_constants(vehicle_id: int, constants_data: VehicleConstantsCreate, db: Session = Depends(get_db_session)):
    """Create a new version of vehicle constants"""
    # Verify vehicle exists
    vehicle = db.query(Vehicle).get(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    # Get preset
    preset = db.query(VehicleConstantsPreset).get(constants_data.preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    
    # Get next version number
    max_version = db.query(db.func.max(VehicleConstants.version)).filter_by(
        vehicle_id=vehicle_id
    ).scalar() or 0
    
    # Create new constants version
    new_constants = VehicleConstants(
        vehicle_id=vehicle_id,
        preset_id=constants_data.preset_id,
        version=max_version + 1,
        note=constants_data.note,
        created_by=1  # TODO: Get from auth
    )
    
    # Apply overrides if provided
    overrides = constants_data.overrides.dict(exclude_unset=True)
    if overrides:
        new_constants.override_vehicle_mass = overrides.get('vehicle_mass')
        new_constants.override_driver_fuel_estimate = overrides.get('driver_fuel_estimate')
        new_constants.override_drag_coefficient = overrides.get('drag_coefficient')
        new_constants.override_frontal_area = overrides.get('frontal_area')
        new_constants.override_rolling_resistance = overrides.get('rolling_resistance')
        new_constants.override_air_density = overrides.get('air_density')
        new_constants.override_wheel_radius = overrides.get('wheel_radius')
        new_constants.override_drivetrain_efficiency = overrides.get('drivetrain_efficiency')
        new_constants.override_road_grade = overrides.get('road_grade')
        new_constants.override_gravity = overrides.get('gravity')
        if 'gear_ratios' in overrides:
            new_constants.override_gear_ratios = json.dumps(overrides['gear_ratios'])
        new_constants.override_final_drive_ratio = overrides.get('final_drive_ratio')
    
    # Deactivate previous versions and set this as active
    db.query(VehicleConstants).filter_by(vehicle_id=vehicle_id).update({'is_active': False})
    new_constants.is_active = True
    
    db.add(new_constants)
    db.commit()
    
    return new_constants.to_dict()

@app.put("/api/vehicles/{vehicle_id}/constants/{constants_id}/activate")
async def activate_vehicle_constants(vehicle_id: int, constants_id: int, db: Session = Depends(get_db_session)):
    """Activate a specific version of vehicle constants"""
    constants = db.query(VehicleConstants).filter_by(
        id=constants_id, vehicle_id=vehicle_id
    ).first()
    if not constants:
        raise HTTPException(status_code=404, detail="Constants not found")
    
    # Deactivate all versions
    db.query(VehicleConstants).filter_by(vehicle_id=vehicle_id).update({'is_active': False})
    
    # Activate selected version
    constants.is_active = True
    db.commit()
    
    return constants.to_dict()

@app.post("/api/vehicles/{vehicle_id}/constants/restore-defaults")
async def restore_default_constants(vehicle_id: int, db: Session = Depends(get_db_session)):
    """Restore vehicle to default Mazda preset"""
    # Find Mazda preset
    mazda_preset = db.query(VehicleConstantsPreset).filter_by(
        manufacturer='Mazda',
        model='3 MPS',
        year=2011,
        chassis='BL'
    ).first()
    
    if not mazda_preset:
        raise HTTPException(status_code=404, detail="Mazda preset not found")
    
    # Create new constants with preset defaults
    # Verify vehicle exists
    vehicle = db.query(Vehicle).get(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    # Get next version number
    max_version = db.query(db.func.max(VehicleConstants.version)).filter_by(
        vehicle_id=vehicle_id
    ).scalar() or 0
    
    # Create new constants version
    new_constants = VehicleConstants(
        vehicle_id=vehicle_id,
        preset_id=mazda_preset.id,
        version=max_version + 1,
        note='Restored to Mazda defaults',
        created_by=1  # TODO: Get from auth
    )
    
    # Deactivate previous versions and set this as active
    db.query(VehicleConstants).filter_by(vehicle_id=vehicle_id).update({'is_active': False})
    new_constants.is_active = True
    
    db.add(new_constants)
    db.commit()
    
    return new_constants.to_dict()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
