"""Virtual Dyno Service Layer

Integrates the dyno engine with telemetry data and database persistence.
"""

import logging
import math
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import json

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from muts.dyno.engine import DynoEngine, VehicleConfig
from muts.dyno.dsg_shift_detector import DSGShiftDetector, ShiftEvent, DynoSegment
from muts.models.database_models import (
    Vehicle, TelemetrySession, DynoRun, DynoSample,
    VehicleConstants, VehicleConstantsPreset, DynoShiftEvent,
    ECUData
)

logger = logging.getLogger(__name__)


class DynoService:
    """Service layer for virtual dyno operations"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def create_dyno_run(self, 
                       vehicle_id: str,
                       telemetry_session_id: int,
                       tuning_profile_id: Optional[int] = None,
                       vehicle_config: Optional[VehicleConfig] = None) -> DynoRun:
        """Create a new dyno run"""
        
        # Get vehicle and session
        vehicle = self.db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        if not vehicle:
            raise ValueError(f"Vehicle {vehicle_id} not found")
        
        session = self.db.query(TelemetrySession).filter(
            TelemetrySession.id == telemetry_session_id
        ).first()
        if not session:
            raise ValueError(f"Telemetry session {telemetry_session_id} not found")
        
        # Get active vehicle constants
        active_constants = self.db.query(VehicleConstants).filter_by(
            vehicle_id=vehicle_id, is_active=True
        ).first()
        
        if not active_constants:
            raise ValueError(f"No active vehicle constants found for vehicle {vehicle_id}")
        
        # Create dyno run record with vehicle_constants_id
        dyno_run = DynoRun(
            vehicle_id=vehicle_id,
            telemetry_session_id=telemetry_session_id,
            tuning_profile_id=tuning_profile_id,
            vehicle_constants_id=active_constants.id,
            status='PENDING'
        )
        
        self.db.add(dyno_run)
        self.db.commit()
        self.db.refresh(dyno_run)
        
        return dyno_run
    
    def process_dyno_run(self, dyno_run_id: int) -> Dict:
        """Process a dyno run from telemetry data"""
        
        # Get dyno run
        dyno_run = self.db.query(DynoRun).filter(DynoRun.id == dyno_run_id).first()
        if not dyno_run:
            raise ValueError(f"Dyno run {dyno_run_id} not found")
        
        try:
            # Update status to recording
            dyno_run.status = 'RECORDING'
            self.db.commit()
            
            # Load telemetry data
            samples = self._load_telemetry_samples(dyno_run.telemetry_session_id)
            
            if len(samples) == 0:
                dyno_run.status = 'REJECTED'
                dyno_run.rejection_reason = 'No telemetry data available'
                self.db.commit()
                return {'status': 'REJECTED', 'reason': 'No telemetry data'}
            
            # Create dyno engine with vehicle config from database
            vehicle_constants = self.db.query(VehicleConstants).get(dyno_run.vehicle_constants_id)
            if not vehicle_constants:
                dyno_run.status = 'REJECTED'
                dyno_run.rejection_reason = 'Vehicle constants not found'
                self.db.commit()
                return {'status': 'REJECTED', 'reason': 'Vehicle constants not found'}
            
            # Get effective constants (preset with overrides)
            constants_dict = vehicle_constants.get_effective_constants()
            
            # Create VehicleConfig from database constants
            config = VehicleConfig.from_db_constants(constants_dict)
            
            engine = DynoEngine(config)
            
            # Detect DSG shifts if applicable
            shift_events = []
            segments = []
            if config.transmission_type == 'DSG':
                detector = DSGShiftDetector()
                shift_events, segments = detector.detect_shifts(samples, config.tire_radius)
                
                # Store shift events in database
                for shift in shift_events:
                    db_shift = DynoShiftEvent(
                        dyno_run_id=dyno_run_id,
                        timestamp_start=shift.timestamp_start,
                        timestamp_end=shift.timestamp_end,
                        timestamp_peak=shift.timestamp_peak,
                        gear_ratio_before=shift.gear_ratio_before,
                        gear_ratio_after=shift.gear_ratio_after,
                        ratio_change_rate=shift.max_change_rate,
                        shift_type=shift.shift_type,
                        confidence=shift.confidence,
                        detection_threshold=detector.ratio_change_threshold,
                        guard_window=detector.guard_window
                    )
                    self.db.add(db_shift)
                
                logger.info(f"Detected {len(shift_events)} DSG shifts and {len(segments)} segments")
            
            # Process the session
            result = engine.process_session(samples)
            
            # Store samples
            self._store_samples(dyno_run_id, samples, result['results'])
            
            # Update dyno run with results
            if result['status'] == 'ACCEPTED':
                dyno_run.status = 'ACCEPTED'
                dyno_run.sample_count = result['sample_count']
                dyno_run.valid_sample_count = result['valid_sample_count']
                dyno_run.data_quality_score = result['data_quality_score']
                
                # Store curves
                dyno_run.set_torque_curve(result['torque_curve'])
                dyno_run.set_power_curve(result['power_curve'])
                
                # Store peaks
                dyno_run.peak_torque = result['peak_torque']
                dyno_run.peak_torque_rpm = result['peak_torque_rpm']
                dyno_run.peak_power = result['peak_power']
                dyno_run.peak_power_rpm = result['peak_power_rpm']
                
                # Detect and store gear ratio
                if result['torque_curve']:
                    # Use median RPM for gear detection
                    median_rpm = sorted([t[0] for t in result['torque_curve']])[len(result['torque_curve']) // 2]
                    dyno_run.gear_ratio = self._estimate_gear_ratio(median_rpm, samples)
                
                # Store pull detection info
                if result['pulls_detected'] > 0:
                    pull_times = self._find_pull_times(samples)
                    if pull_times:
                        dyno_run.pull_start_time = pull_times[0][0]
                        dyno_run.pull_end_time = pull_times[-1][1]
                        dyno_run.pull_start_rpm = self._get_rpm_at_time(samples, pull_times[0][0])
                        dyno_run.pull_end_rpm = self._get_rpm_at_time(samples, pull_times[-1][1])
                
            else:
                dyno_run.status = 'REJECTED'
                dyno_run.rejection_reason = result['rejection_reason']
            
            # Update safety flags
            self._update_safety_flags(dyno_run, samples)
            
            self.db.commit()
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing dyno run {dyno_run_id}: {e}")
            dyno_run.status = 'REJECTED'
            dyno_run.rejection_reason = f"Processing error: {str(e)}"
            self.db.commit()
            return {'status': 'ERROR', 'error': str(e)}
    
    def _load_telemetry_samples(self, session_id: int) -> List[TelemetrySample]:
        """Load telemetry samples from database"""
        
        # Query ECU data for the session
        ecu_data = self.db.query(ECUData).filter(
            ECUData.vehicle_id == TelemetrySession.vehicle_id
        ).all()
        
        # Note: In a real implementation, we'd query by session time range
        # For now, load all available data
        samples = []
        
        for data in ecu_data:
            # Convert km/h to m/s
            speed_ms = (data.speed or 0) * 1000 / 3600
            
            sample = TelemetrySample(
                timestamp=data.timestamp.timestamp() if data.timestamp else 0,
                rpm=data.rpm or 0,
                vehicle_speed=speed_ms,
                throttle_position=data.throttle_position or 0,
                boost_pressure=data.boost_pressure or 0,
                afr=data.afr or 14.7,
                ignition_timing=data.ignition_timing or 0,
                engine_load=data.calculated_load or 0,
                intake_temp=data.intake_air_temp or 20,
                coolant_temp=data.coolant_temp or 20
            )
            samples.append(sample)
        
        # Sort by timestamp
        samples.sort(key=lambda x: x.timestamp)
        
        return samples
    
    def _store_samples(self, dyno_run_id: int, raw_samples: List[TelemetrySample], 
                      results: List[Dict]) -> None:
        """Store individual samples with calculated values"""
        
        # Create mapping of timestamp to result
        result_map = {r['timestamp']: r for r in results}
        
        for i, sample in enumerate(raw_samples):
            dyno_sample = DynoSample(
                dyno_run_id=dyno_run_id,
                timestamp=sample.timestamp,
                rpm=sample.rpm,
                vehicle_speed=sample.vehicle_speed,
                throttle_position=sample.throttle_position,
                boost_pressure=sample.boost_pressure,
                afr=sample.afr,
                ignition_timing=sample.ignition_timing,
                engine_load=sample.engine_load,
                intake_temp=sample.intake_temp,
                coolant_temp=sample.coolant_temp
            )
            
            # Add calculated values if available
            if sample.timestamp in result_map:
                result = result_map[sample.timestamp]
                # Convert DynoResult to dict for storage
                if hasattr(result, '__dict__'):
                    result_dict = result.__dict__
                else:
                    result_dict = result
                    
                dyno_sample.acceleration = result_dict.get('acceleration', 0)
                dyno_sample.wheel_torque = result_dict.get('wheel_torque', 0)
                dyno_sample.engine_torque = result_dict.get('engine_torque', 0)
                dyno_sample.wheel_power = result_dict.get('wheel_power', 0)
                dyno_sample.engine_power = result_dict.get('engine_power', 0)
                dyno_sample.force_tractive = result_dict.get('force_tractive', 0)
                dyno_sample.force_rolling_resistance = result_dict.get('force_rolling_resistance', 0)
                dyno_sample.force_aerodynamic = result_dict.get('force_aerodynamic', 0)
                dyno_sample.force_grade = result_dict.get('force_grade', 0)
                dyno_sample.gear_ratio = result_dict.get('gear_ratio', 0)
                dyno_sample.is_valid = result_dict.get('is_valid', False)
                dyno_sample.set_rejection_flags(result_dict.get('rejection_flags', []))
            
            self.db.add(dyno_sample)
        
        self.db.commit()
    
    def _update_safety_flags(self, dyno_run: DynoRun, samples: List[TelemetrySample]) -> None:
        """Update safety flags based on samples"""
        
        if not samples:
            return
        
        # Check for extreme values
        max_coolant = max(s.coolant_temp for s in samples)
        max_intake = max(s.intake_temp for s in samples)
        min_afr = min(s.afr for s in samples)
        max_boost = max(s.boost_pressure for s in samples)
        
        dyno_run.max_coolant_temp = max_coolant
        dyno_run.max_intake_temp = max_intake
        dyno_run.min_afr = min_afr
        dyno_run.max_boost = max_boost
        
        # Set flags
        dyno_run.over_temp_detected = max_coolant > 110 or max_intake > 80
        dyno_run.unsafe_afr_detected = min_afr < 11.5 or min_afr > 15.0
        
        # Note: Knock detection would need knock sensor data
        dyno_run.knock_detected = False
    
    def _estimate_gear_ratio(self, rpm: float, samples: List[TelemetrySample]) -> Optional[float]:
        """Estimate gear ratio from RPM and speed"""
        
        # Find sample closest to target RPM
        closest_sample = min(samples, key=lambda s: abs(s.rpm - rpm))
        
        if closest_sample.vehicle_speed > 0:
            wheel_rpm = (closest_sample.vehicle_speed * 60) / (2 * math.pi * self.default_config.tire_radius)
            if wheel_rpm > 0:
                return closest_sample.rpm / wheel_rpm / self.default_config.final_drive_ratio
        
        return None
    
    def _find_pull_times(self, samples: List[TelemetrySample]) -> List[Tuple[float, float]]:
        """Find pull time windows"""
        # Simplified - find WOT segments
        pulls = []
        in_pull = False
        pull_start = 0
        
        for sample in samples:
            if sample.throttle_position >= 95 and sample.rpm >= 2000 and sample.rpm <= 6500:
                if not in_pull:
                    pull_start = sample.timestamp
                    in_pull = True
            else:
                if in_pull:
                    pulls.append((pull_start, sample.timestamp))
                    in_pull = False
        
        return pulls
    
    def _get_rpm_at_time(self, samples: List[TelemetrySample], time: float) -> Optional[float]:
        """Get RPM at specific time"""
        for sample in samples:
            if abs(sample.timestamp - time) < 0.1:
                return sample.rpm
        return None
    
    def get_dyno_runs(self, vehicle_id: Optional[str] = None) -> List[Dict]:
        """Get dyno runs with results"""
        
        query = self.db.query(DynoRun)
        if vehicle_id:
            query = query.filter(DynoRun.vehicle_id == vehicle_id)
        
        runs = query.order_by(DynoRun.run_time.desc()).all()
        
        return [run.to_dict() for run in runs]
    
    def get_dyno_run(self, run_id: int) -> Optional[Dict]:
        """Get detailed dyno run with samples"""
        
        run = self.db.query(DynoRun).filter(DynoRun.id == run_id).first()
        if not run:
            return None
        
        result = run.to_dict()
        
        # Add samples
        samples = self.db.query(DynoSample).filter(
            DynoSample.dyno_run_id == run_id
        ).order_by(DynoSample.timestamp).all()
        
        result['samples'] = [s.to_dict() for s in samples]
        
        return result
    
    def compare_runs(self, run1_id: int, run2_id: int) -> Dict:
        """Compare two dyno runs (before/after tune)"""
        
        run1 = self.get_dyno_run(run1_id)
        run2 = self.get_dyno_run(run2_id)
        
        if not run1 or not run2:
            raise ValueError("One or both runs not found")
        
        comparison = {
            'run1': run1,
            'run2': run2,
            'differences': {}
        }
        
        # Calculate differences
        if run1['status'] == 'ACCEPTED' and run2['status'] == 'ACCEPTED':
            comparison['differences'] = {
                'peak_torque_change': run2['peak_torque'] - run1['peak_torque'],
                'peak_torque_rpm_change': run2['peak_torque_rpm'] - run1['peak_torque_rpm'],
                'peak_power_change': run2['peak_power'] - run1['peak_power'],
                'peak_power_rpm_change': run2['peak_power_rpm'] - run1['peak_power_rpm'],
                'torque_curve_delta': self._calculate_curve_delta(
                    run1['torque_curve'], run2['torque_curve']
                ),
                'power_curve_delta': self._calculate_curve_delta(
                    run1['power_curve'], run2['power_curve']
                )
            }
        
        return comparison
    
    def _calculate_curve_delta(self, curve1: List[Dict], curve2: List[Dict]) -> List[Dict]:
        """Calculate difference between two curves"""
        
        # Interpolate curves to common RPM points
        rpm_points = list(range(2000, 6501, 100))
        delta = []
        
        for rpm in rpm_points:
            val1 = self._interpolate_curve(curve1, rpm)
            val2 = self._interpolate_curve(curve2, rpm)
            
            if val1 is not None and val2 is not None:
                delta.append({'rpm': rpm, 'delta': val2 - val1})
        
        return delta
    
    def _interpolate_curve(self, curve: List[Dict], rpm: float) -> Optional[float]:
        """Interpolate value at specific RPM"""
        
        if not curve:
            return None
        
        # Find surrounding points
        before = None
        after = None
        
        for point in curve:
            if point['rpm'] <= rpm:
                before = point
            if point['rpm'] >= rpm and after is None:
                after = point
                break
        
        if before and after:
            if before['rpm'] == after['rpm']:
                return before['torque'] if 'torque' in before else before['power']
            
            # Linear interpolation
            t = (rpm - before['rpm']) / (after['rpm'] - before['rpm'])
            val1 = before['torque'] if 'torque' in before else before['power']
            val2 = after['torque'] if 'torque' in after else after['power']
            return val1 + t * (val2 - val1)
        
        return None
