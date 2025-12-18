"""Virtual Dyno Calculation Engine

Physics-based torque and power calculations from real telemetry data.
No fake values, no assumptions - only physics and real data.
"""

import math
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class VehicleConfig:
    """Vehicle configuration for dyno calculations"""
    vehicle_mass: float  # kg
    drivetrain_loss: float  # percentage
    tire_radius: float  # meters
    final_drive_ratio: float
    gear_ratios: Dict[int, float]  # gear number -> ratio
    rolling_resistance: float
    drag_coefficient: float
    frontal_area: float
    air_density: float
    road_grade: float = 0.0  # degrees
    gravity: float = 9.81  # m/s^2
    transmission_type: Optional[str] = None  # MANUAL, DSG, TORQUE_CONVERTER, CVT
    drivetrain_type: Optional[str] = None  # FWD, RWD, AWD_HALDEX, AWD_FULL, AWD_PART_TIME
    awd_torque_split_front: Optional[float] = None  # 0-1 for AWD vehicles
    awd_torque_split_rear: Optional[float] = None  # 0-1 for AWD vehicles
    coupling_loss_factor: Optional[float] = None  # Additional loss for AWD coupling

    @classmethod
    def from_db_constants(cls, constants_dict: Dict) -> 'VehicleConfig':
        """Create VehicleConfig from database constants dictionary"""
        return cls(
            vehicle_mass=constants_dict['total_mass'],  # Use total mass (vehicle + driver + fuel)
            drivetrain_loss=(1 - constants_dict['drivetrain_efficiency']) * 100,  # Convert to percentage
            tire_radius=constants_dict['wheel_radius'],
            final_drive_ratio=constants_dict['final_drive_ratio'],
            gear_ratios={i+1: ratio for i, ratio in enumerate(constants_dict['gear_ratios'])},
            rolling_resistance=constants_dict['rolling_resistance'],
            drag_coefficient=constants_dict['drag_coefficient'],
            frontal_area=constants_dict['frontal_area'],
            air_density=constants_dict['air_density'],
            road_grade=constants_dict.get('road_grade', 0.0),
            gravity=constants_dict.get('gravity', 9.81),
            transmission_type=constants_dict.get('transmission_type'),
            drivetrain_type=constants_dict.get('drivetrain_type'),
            awd_torque_split_front=constants_dict.get('awd_torque_split_front'),
            awd_torque_split_rear=constants_dict.get('awd_torque_split_rear'),
            coupling_loss_factor=constants_dict.get('coupling_loss_factor')
        )


@dataclass
class TelemetrySample:
    """Single telemetry sample with all required inputs"""
    timestamp: float  # seconds from start
    rpm: float
    vehicle_speed: float  # m/s
    throttle_position: float  # 0-100%
    boost_pressure: float  # kPa gauge
    afr: float  # lambda or afr
    ignition_timing: float  # degrees BTDC
    engine_load: float  # 0-100%
    intake_temp: float  # Celsius
    coolant_temp: float  # Celsius
    rpm_change_rate: Optional[float] = None  # RPM/s for shift detection


@dataclass
class DynoResult:
    """Single dyno calculation result"""
    timestamp: float
    rpm: float
    acceleration: float  # m/s^2
    wheel_torque: float  # Nm
    engine_torque: float  # Nm
    wheel_power: float  # kW
    engine_power: float  # kW
    force_tractive: float  # N
    force_rolling_resistance: float  # N
    force_aerodynamic: float  # N
    force_grade: float  # N
    gear_ratio: float
    is_valid: bool
    rejection_flags: List[str]
    # AWD torque split
    torque_front: Optional[float] = None  # Nm
    torque_rear: Optional[float] = None   # Nm
    # Efficiency tracking
    drivetrain_efficiency_actual: Optional[float] = None  # Actual efficiency used


class SafetyValidator:
    """Validates telemetry samples for safety violations"""
    
    def __init__(self):
        self.max_coolant_temp = 110.0  # Celsius
        self.max_intake_temp = 80.0  # Celsius
        self.min_afr_turbo = 11.5  # AFR (turbo engine)
        self.max_afr_turbo = 15.0  # AFR
        self.max_boost_kpa = 200.0  # kPa gauge (about 29 psi)
        self.max_knock_count = 5  # per sample window
    
    def validate_sample(self, sample: TelemetrySample) -> Tuple[bool, List[str]]:
        """Validate a single telemetry sample"""
        flags = []
        
        # Temperature checks
        if sample.coolant_temp > self.max_coolant_temp:
            flags.append(f"Over-temp coolant: {sample.coolant_temp:.1f}°C")
        
        if sample.intake_temp > self.max_intake_temp:
            flags.append(f"Over-temp intake: {sample.intake_temp:.1f}°C")
        
        # AFR checks (assuming AFR, not lambda)
        if sample.afr < self.min_afr_turbo:
            flags.append(f"Unsafe lean AFR: {sample.afr:.1f}")
        elif sample.afr > self.max_afr_turbo:
            flags.append(f"Unsafe rich AFR: {sample.afr:.1f}")
        
        # Boost check
        if sample.boost_pressure > self.max_boost_kpa:
            flags.append(f"Over-boost: {sample.boost_pressure:.1f} kPa")
        
        # Throttle position (must be WOT for valid pull)
        if sample.throttle_position < 95.0:
            flags.append(f"Throttle not WOT: {sample.throttle_position:.1f}%")
        
        return len(flags) == 0, flags


class PullDetector:
    """Detects valid pull windows in telemetry data"""
    
    def __init__(self, min_rpm: float = 2000, max_rpm: float = 6500):
        self.min_rpm = min_rpm
        self.max_rpm = max_rpm
        self.min_duration = 2.0  # seconds
        self.min_acceleration = 1.0  # m/s^2
        self.wheelslip_threshold = 0.3  # 30% speed drop while RPM climbs
        
    def detect_pulls(self, samples: List[TelemetrySample]) -> List[Tuple[int, int]]:
        """Detect valid pull windows as (start_idx, end_idx)"""
        if len(samples) < 10:
            return []
        
        pulls = []
        in_pull = False
        pull_start = 0
        
        for i, sample in enumerate(samples):
            # Check if we're in pull conditions
            if (sample.rpm >= self.min_rpm and 
                sample.rpm <= self.max_rpm and
                sample.throttle_position >= 85.0):  # Changed from 95 to 85 per requirements
                
                if not in_pull:
                    # Start of potential pull
                    in_pull = True
                    pull_start = i
            else:
                if in_pull:
                    # End of pull
                    pull_end = i - 1
                    if pull_end - pull_start >= 10:  # Minimum samples
                        pulls.append((pull_start, pull_end))
                    in_pull = False
        
        # Handle pull at end of data
        if in_pull:
            pull_end = len(samples) - 1
            if pull_end - pull_start >= 10:
                pulls.append((pull_start, pull_end))
        
        # Validate pulls have sufficient acceleration and stable conditions
        valid_pulls = []
        for start, end in pulls:
            if self._validate_pull_conditions(samples[start:end+1]):
                valid_pulls.append((start, end))
        
        return valid_pulls
    
    def _validate_pull_conditions(self, samples: List[TelemetrySample]) -> bool:
        """Check if pull has sufficient acceleration and stable conditions"""
        if len(samples) < 2:
            return False
        
        # Check 1: Average acceleration
        accel_sum = 0
        for i in range(1, len(samples)):
            dt = samples[i].timestamp - samples[i-1].timestamp
            if dt > 0:
                dv = samples[i].vehicle_speed - samples[i-1].vehicle_speed
                accel_sum += dv / dt
        
        avg_accel = accel_sum / (len(samples) - 1)
        if avg_accel < self.min_acceleration:
            return False
        
        # Check 2: Monotonic RPM increase
        for i in range(1, len(samples)):
            if samples[i].rpm < samples[i-1].rpm:
                return False  # RPM dropped
        
        # Check 3: No wheelspin (speed drops while RPM climbs)
        for i in range(2, len(samples)):
            if samples[i].rpm > samples[i-1].rpm:  # RPM increasing
                speed_drop_ratio = (samples[i-1].vehicle_speed - samples[i].vehicle_speed) / samples[i-1].vehicle_speed
                if speed_drop_ratio > self.wheelslip_threshold:
                    return False  # Potential wheelspin
        
        # Check 4: Stable gear ratio
        gear_ratios = []
        for i in range(1, len(samples)):
            if samples[i].vehicle_speed > 0:
                wheel_rpm = (samples[i].vehicle_speed * 60) / (2 * math.pi * 0.3175)  # Default tire radius
                if wheel_rpm > 0:
                    ratio = samples[i].rpm / wheel_rpm
                    gear_ratios.append(ratio)
        
        if len(gear_ratios) > 0:
            ratio_variance = np.var(gear_ratios)
            if ratio_variance > 0.1:  # Ratio too unstable
                return False
        
        return True


class DynoEngine:
    """Main dyno calculation engine"""
    
    # Physics constants
    AIR_DENSITY = 1.225  # kg/m^3 at sea level
    GRAVITY = 9.81  # m/s^2
    
    def __init__(self, config: VehicleConfig):
        self.config = config
        self.safety_validator = SafetyValidator()
        self.pull_detector = PullDetector()
        
    def calculate_torque_and_power(self, samples: List[TelemetrySample]) -> List[DynoResult]:
        """Calculate torque and power from telemetry samples"""
        results = []
        
        for i, sample in enumerate(samples):
            # Safety validation first
            is_safe, flags = self.safety_validator.validate_sample(sample)
            
            if not is_safe:
                results.append(DynoResult(
                    timestamp=sample.timestamp,
                    rpm=sample.rpm,
                    acceleration=0,
                    wheel_torque=0,
                    engine_torque=0,
                    wheel_power=0,
                    engine_power=0,
                    force_tractive=0,
                    force_rolling_resistance=0,
                    force_aerodynamic=0,
                    force_grade=0,
                    gear_ratio=0,
                    is_valid=False,
                    rejection_flags=flags
                ))
                continue
            
            # Calculate acceleration using central difference
            acceleration = 0
            if i > 0 and i < len(samples) - 1:
                dt_forward = samples[i+1].timestamp - samples[i].timestamp
                dt_backward = samples[i].timestamp - samples[i-1].timestamp
                if dt_forward > 0 and dt_backward > 0:
                    dv_forward = samples[i+1].vehicle_speed - samples[i].vehicle_speed
                    dv_backward = samples[i].vehicle_speed - samples[i-1].vehicle_speed
                    acceleration = (dv_forward/dt_forward + dv_backward/dt_backward) / 2
            elif i == 0 and len(samples) > 1:
                # Forward difference for first point
                dt = samples[1].timestamp - samples[0].timestamp
                if dt > 0:
                    acceleration = (samples[1].vehicle_speed - samples[0].vehicle_speed) / dt
            elif i == len(samples) - 1 and len(samples) > 1:
                # Backward difference for last point
                dt = samples[i].timestamp - samples[i-1].timestamp
                if dt > 0:
                    acceleration = (samples[i].vehicle_speed - samples[i-1].vehicle_speed) / dt
            
            # Calculate individual force components
            # Rolling resistance force: F_rr = m * g * Crr
            force_rolling = self.config.vehicle_mass * self.GRAVITY * self.config.rolling_resistance
            
            # Aerodynamic drag: F_d = 0.5 * ρ * Cd * A * v²
            force_aero = 0.5 * self.config.air_density * self.config.drag_coefficient * \
                       self.config.frontal_area * sample.vehicle_speed ** 2
            
            # Grade force: F_g = m * g * sin(θ)
            force_grade = self.config.vehicle_mass * self.GRAVITY * \
                        math.sin(math.radians(self.config.road_grade))
            
            # Total tractive force: F_trac = m * a + F_rr + F_d + F_g
            force_tractive = self.config.vehicle_mass * acceleration + force_rolling + force_aero + force_grade
            
            # Wheel torque: T_wheel = F_trac * r_w
            wheel_torque = force_tractive * self.config.tire_radius
            
            # Wheel power: P_wheel = F_trac * v
            wheel_power_watts = force_tractive * sample.vehicle_speed
            wheel_power_kw = wheel_power_watts / 1000
            
            # Calculate engine torque (accounting for drivetrain)
            total_ratio = self._get_total_gear_ratio(sample)
            if total_ratio > 0:
                # Calculate actual drivetrain efficiency with AWD loss model
                drivetrain_efficiency_actual = self._calculate_drivetrain_efficiency()
                
                wheel_torque = force_tractive * self.config.tire_radius
                engine_torque = wheel_torque / total_ratio / drivetrain_efficiency_actual
                wheel_power_watts = force_tractive * sample.vehicle_speed
                engine_power_watts = wheel_power_watts / drivetrain_efficiency_actual
                
                # Calculate AWD torque split if applicable
                torque_front = None
                torque_rear = None
                
                if self.config.drivetrain_type in ['AWD_HALDEX', 'AWD_FULL', 'AWD_PART_TIME']:
                    if self.config.awd_torque_split_front is not None:
                        torque_front = wheel_torque * self.config.awd_torque_split_front
                    if self.config.awd_torque_split_rear is not None:
                        torque_rear = wheel_torque * self.config.awd_torque_split_rear
            else:
                engine_torque = 0
                engine_power_watts = 0
                drivetrain_efficiency_actual = self.config.drivetrain_efficiency / 100
                torque_front = None
                torque_rear = None
            
            engine_power_kw = engine_power_watts / 1000
            
            results.append(DynoResult(
                timestamp=sample.timestamp,
                rpm=sample.rpm,
                acceleration=acceleration,
                wheel_torque=wheel_torque,
                engine_torque=engine_torque,
                wheel_power=wheel_power_kw,
                engine_power=engine_power_kw,
                force_tractive=force_tractive,
                force_rolling_resistance=force_rolling,
                force_aerodynamic=force_aero,
                force_grade=force_grade,
                gear_ratio=total_ratio,
                is_valid=True,
                rejection_flags=[],
                torque_front=torque_front,
                torque_rear=torque_rear,
                drivetrain_efficiency_actual=drivetrain_efficiency_actual
            ))
        
        return results
    
    def _get_previous_speed(self, samples: List[TelemetrySample], current_time: float) -> float:
        """Get speed from previous sample"""
        for sample in reversed(samples):
            if sample.timestamp < current_time:
                return sample.vehicle_speed
        return 0
    
    def _calculate_traction_force(self, sample: TelemetrySample, acceleration: float) -> float:
        """Calculate traction force at wheels"""
        # F = ma + rolling resistance + aerodynamic drag
        mass_force = self.config.vehicle_mass * acceleration
        
        # Rolling resistance
        rolling_force = self.config.rolling_resistance * self.config.vehicle_mass * self.GRAVITY
        
        # Aerodynamic drag
        drag_force = 0.5 * self.AIR_DENSITY * self.config.frontal_area * \
                   self.config.drag_coefficient * sample.vehicle_speed ** 2
        
        # Total traction force
        traction_force = mass_force + rolling_force + drag_force
        
        return traction_force
    
    def _get_total_gear_ratio(self, sample: TelemetrySample) -> float:
        """Get total gear ratio (gear * final drive)"""
        # Estimate gear from RPM and speed
        wheel_rpm = (sample.vehicle_speed * 60) / (2 * math.pi * self.config.tire_radius)
        engine_wheel_ratio = sample.rpm / wheel_rpm if wheel_rpm > 0 else 0
        
        # Find closest gear
        closest_gear = None
        min_diff = float('inf')
        
        for gear, gear_ratio in self.config.gear_ratios.items():
            total_ratio = gear_ratio * self.config.final_drive_ratio
            diff = abs(total_ratio - engine_wheel_ratio)
            if diff < min_diff:
                min_diff = diff
                closest_gear = gear
        
        # DSG-specific adjustments
        if closest_gear is not None and hasattr(self.config, 'transmission_type'):
            if self.config.transmission_type == 'DSG':
                # DSG may have slight torque converter slip during shifts
                # Be more tolerant with gear detection for DSG
                tolerance = 0.5
            else:
                tolerance = 0.3
        else:
            tolerance = 0.5
        
        if closest_gear is not None and min_diff < tolerance:
            total_ratio = self.config.gear_ratios[closest_gear] * self.config.final_drive_ratio
            
            # Apply DSG shift compensation if needed
            if hasattr(self.config, 'transmission_type') and self.config.transmission_type == 'DSG':
                if self._is_shifting_dsg(sample):
                    total_ratio *= 0.98  # Account for 2% slip during shifts
            
            return total_ratio
        
        return 0
    
    def _calculate_drivetrain_efficiency(self) -> float:
        """Calculate actual drivetrain efficiency with AWD loss model"""
        base_efficiency = self.config.drivetrain_efficiency / 100
        
        # For AWD vehicles, apply coupling loss
        if (self.config.drivetrain_type in ['AWD_HALDEX', 'AWD_FULL', 'AWD_PART_TIME'] and 
            self.config.coupling_loss_factor is not None and 
            self.config.awd_torque_split_front is not None):
            
            # η_eff = η_base - k_coupling * (1 - α_front)
            # Where α_front is front torque fraction
            alpha = self.config.awd_torque_split_front
            coupling_loss = self.config.coupling_loss_factor * (1 - alpha)
            actual_efficiency = base_efficiency - coupling_loss
            
            return max(0.5, min(1.0, actual_efficiency))  # Clamp between 0.5 and 1.0
        
        return base_efficiency
    
    def _is_shifting_dsg(self, sample: TelemetrySample) -> bool:
        """Detect if DSG transmission is currently shifting"""
        # Simple shift detection based on rapid RPM changes
        # In a real implementation, this would use more sophisticated detection
        if hasattr(sample, 'rpm_change_rate'):
            return sample.rpm_change_rate > 100  # RPM changing faster than 100 RPM/s
        return False
    
    def calculate_confidence_score(self, samples: List[TelemetrySample], results: List[DynoResult], 
                                shift_events: Optional[List] = None) -> Dict:
        """Calculate confidence score based on data quality metrics"""
        if not samples or not results:
            return {'score': 0, 'rating': 'LOW', 'factors': []}
        
        factors = []
        score = 100
        
        # Factor 1: Sample count (more samples = higher confidence)
        sample_count = len(results)
        if sample_count < 20:
            score -= 30
            factors.append('Low sample count (< 20)')
        elif sample_count < 50:
            score -= 15
            factors.append('Moderate sample count (< 50)')
        
        # Factor 2: Data quality (percentage of valid samples)
        valid_samples = sum(1 for r in results if r.is_valid)
        if valid_samples == 0:
            score -= 50
            factors.append('No valid samples')
        else:
            quality_ratio = valid_samples / len(results)
            if quality_ratio < 0.8:
                score -= 20
                factors.append('Low data quality (< 80% valid)')
            elif quality_ratio < 0.95:
                score -= 10
                factors.append('Moderate data quality (< 95% valid)')
        
        # Factor 3: RPM monotonicity
        rpm_drops = 0
        for i in range(1, len(samples)):
            if samples[i].rpm < samples[i-1].rpm:
                rpm_drops += 1
        if rpm_drops > 0:
            score -= min(20, rpm_drops * 5)
            factors.append(f'RPM non-monotonic ({rpm_drops} drops)')
        
        # Factor 4: Gear ratio stability
        gear_ratios = [r.gear_ratio for r in results if r.gear_ratio > 0]
        if len(gear_ratios) > 0:
            ratio_variance = np.var(gear_ratios)
            if ratio_variance > 0.5:
                score -= 25
                factors.append('Unstable gear ratio')
            elif ratio_variance > 0.1:
                score -= 10
                factors.append('Moderate gear ratio variance')
        
        # Factor 5: Acceleration consistency
        accelerations = [r.acceleration for r in results if r.is_valid]
        if len(accelerations) > 0:
            accel_variance = np.var(accelerations)
            if accel_variance > 10:
                score -= 15
                factors.append('Inconsistent acceleration')
        
        # Factor 6: Safety margins
        min_afr = min(s.afr for s in samples)
        max_coolant = max(s.coolant_temp for s in samples)
        max_intake = max(s.intake_temp for s in samples)
        
        if min_afr < 12.0:
            score -= 20
            factors.append('Very lean AFR detected')
        elif min_afr < 12.5:
            score -= 10
            factors.append('Lean AFR detected')
        
        if max_coolant > 105:
            score -= 15
            factors.append('High coolant temperature')
        elif max_coolant > 100:
            score -= 5
            factors.append('Elevated coolant temperature')
        
        # Factor 7: DSG shift detection (if applicable)
        if self.config.transmission_type == 'DSG':
            if shift_events and len(shift_events) > 0:
                # Check for unstable segments between shifts
                unstable_segments = 0
                for segment in shift_events:
                    if hasattr(segment, 'is_valid') and not segment.is_valid:
                        unstable_segments += 1
                
                if unstable_segments > 0:
                    score -= min(20, unstable_segments * 10)
                    factors.append(f'Unstable DSG segments ({unstable_segments})')
                
                # Deduct for each shift (shifts reduce confidence)
                score -= min(15, len(shift_events) * 3)
                factors.append(f'DSG shifts detected ({len(shift_events)})')
            else:
                # No shifts detected for DSG is suspicious
                score -= 20
                factors.append('DSG expected but no shifts detected')
        
        # Factor 8: AWD torque split uncertainty
        if self.config.drivetrain_type in ['AWD_HALDEX', 'AWD_FULL', 'AWD_PART_TIME']:
            if self.config.awd_torque_split_front is None:
                score -= 15
                factors.append('AWD torque split unknown')
            elif self.config.coupling_loss_factor is None:
                score -= 10
                factors.append('AWD coupling loss unknown')
            else:
                # Check if torque split is assumed (not from manufacturer data)
                if self.config.awd_torque_split_front == 0.5:  # Default 50/50 split
                    score -= 5
                    factors.append('AWD torque split assumed')
        
        # Ensure score is within bounds
        score = max(0, min(100, score))
        
        # Determine rating
        if score >= 80:
            rating = 'HIGH'
        elif score >= 60:
            rating = 'MEDIUM'
        else:
            rating = 'LOW'
        
        return {
            'score': score,
            'rating': rating,
            'factors': factors
        }
    
    def process_session(self, samples: List[TelemetrySample]) -> Dict:
        """Process a complete telemetry session"""
        if len(samples) == 0:
            return {
                'status': 'REJECTED',
                'rejection_reason': 'No telemetry samples provided',
                'results': []
            }
        
        # Detect valid pulls
        pulls = self.pull_detector.detect_pulls(samples)
        
        if not pulls:
            return {
                'status': 'REJECTED',
                'rejection_reason': 'No valid pulls detected (need WOT acceleration)',
                'results': []
            }
        
        # Process all valid samples from pulls
        all_valid_samples = []
        for start, end in pulls:
            all_valid_samples.extend(samples[start:end+1])
        
        # Calculate torque and power
        results = self.calculate_torque_and_power(all_valid_samples)
        
        # Filter valid results
        valid_results = [r for r in results if r.is_valid]
        
        if len(valid_results) == 0:
            return {
                'status': 'REJECTED',
                'rejection_reason': 'No samples passed safety validation',
                'results': results
            }
        
        # Calculate curves and peaks
        torque_curve = [(r.rpm, r.engine_torque) for r in valid_results]
        power_curve = [(r.rpm, r.engine_power) for r in valid_results]
        
        peak_torque = max(t[1] for t in torque_curve)
        peak_torque_rpm = torque_curve[[t[1] for t in torque_curve].index(peak_torque)][0]
        peak_power = max(p[1] for p in power_curve)
        peak_power_rpm = power_curve[[p[1] for p in power_curve].index(peak_power)][0]
        
        # Calculate data quality score
        data_quality = (len(valid_results) / len(all_valid_samples)) * 100
        
        # Calculate confidence score
        confidence = self.calculate_confidence_score(all_valid_samples, results)
        
        return {
            'status': 'ACCEPTED',
            'pulls_detected': len(pulls),
            'sample_count': len(all_valid_samples),
            'valid_sample_count': len(valid_results),
            'data_quality_score': data_quality,
            'confidence_score': confidence['score'],
            'confidence_rating': confidence['rating'],
            'confidence_factors': confidence['factors'],
            'torque_curve': torque_curve,
            'power_curve': power_curve,
            'peak_torque': peak_torque,
            'peak_torque_rpm': peak_torque_rpm,
            'peak_power': peak_power,
            'peak_power_rpm': peak_power_rpm,
            'results': results
        }
    
    def apply_smoothing(self, curve: List[Tuple[float, float]], window: int = 5) -> List[Tuple[float, float]]:
        """Apply moving average smoothing to curve"""
        if len(curve) < window:
            return curve
        
        smoothed = []
        for i in range(len(curve)):
            start = max(0, i - window // 2)
            end = min(len(curve), i + window // 2 + 1)
            
            avg_rpm = sum(p[0] for p in curve[start:end]) / (end - start)
            avg_value = sum(p[1] for p in curve[start:end]) / (end - start)
            smoothed.append((avg_rpm, avg_value))
        
        return smoothed


# Default configuration is now loaded from database
# No hardcoded constants allowed
