"""
DSG Shift Detection for Virtual Dyno
Detects gear shifts in DSG transmissions using effective gear ratio stability
"""

import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass
from app.muts.dyno.engine import TelemetrySample
import math


@dataclass
class ShiftEvent:
    """Represents a detected shift event"""
    timestamp_start: float  # seconds
    timestamp_end: float    # seconds
    timestamp_peak: float   # seconds
    gear_ratio_before: float
    gear_ratio_after: float
    max_change_rate: float
    shift_type: str  # "UP" or "DOWN"
    confidence: float


@dataclass
class DynoSegment:
    """Represents a segment of dyno data between shifts"""
    start_index: int
    end_index: int
    start_time: float
    end_time: float
    gear_ratio: float
    is_valid: bool
    rejection_reason: Optional[str] = None


class DSGShiftDetector:
    """Detects DSG shifts using effective gear ratio monitoring"""
    
    def __init__(self, 
                 ratio_change_threshold: float = 0.5,
                 guard_window: float = 0.5,
                 min_segment_duration: float = 1.0,
                 smoothing_window: int = 5,
                 throttle_threshold: float = 80.0):
        """
        Initialize DSG shift detector
        
        Args:
            ratio_change_threshold: Minimum |dG_eff/dt| to detect shift (ratio/s)
            guard_window: Time to exclude around detected shifts (seconds)
            min_segment_duration: Minimum valid segment duration (seconds)
            smoothing_window: Window size for derivative smoothing (samples)
            throttle_threshold: Minimum throttle for valid pull detection (%)
        """
        self.ratio_change_threshold = ratio_change_threshold
        self.guard_window = guard_window
        self.min_segment_duration = min_segment_duration
        self.smoothing_window = smoothing_window
        self.throttle_threshold = throttle_threshold
    
    def detect_shifts(self, samples: List[TelemetrySample], wheel_radius: float) -> Tuple[List[ShiftEvent], List[DynoSegment]]:
        """
        Detect shift events in telemetry data
        
        Args:
            samples: List of telemetry samples
            wheel_radius: Wheel radius in meters
            
        Returns:
            Tuple of (shift_events, segments)
        """
        if len(samples) < self.smoothing_window * 2:
            return [], []
        
        # Calculate effective gear ratio and derivatives
        gear_ratios, ratio_derivatives = self._calculate_effective_ratios(samples, wheel_radius)
        
        # Detect shift events
        shift_events = self._find_shift_events(samples, gear_ratios, ratio_derivatives)
        
        # Create segments between shifts
        segments = self._create_segments(samples, shift_events, gear_ratios)
        
        return shift_events, segments
    
    def _calculate_effective_ratios(self, samples: List[TelemetrySample], wheel_radius: float) -> Tuple[List[float], List[float]]:
        """Calculate effective gear ratio and its derivative"""
        gear_ratios = []
        ratio_derivatives = []
        
        for i, sample in enumerate(samples):
            # Calculate wheel angular velocity
            if sample.vehicle_speed > 0 and wheel_radius > 0:
                omega_wheel = sample.vehicle_speed / wheel_radius
            else:
                omega_wheel = 0
            
            # Calculate engine angular velocity
            omega_engine = (sample.rpm * 2 * math.pi) / 60
            
            # Effective gear ratio
            if omega_wheel > 0:
                g_eff = omega_engine / omega_wheel
            else:
                g_eff = 0
            
            gear_ratios.append(g_eff)
            
            # Calculate derivative with smoothing
            if i >= self.smoothing_window:
                # Use central difference with averaging
                deriv = self._calculate_smoothed_derivative(gear_ratios, i)
                ratio_derivatives.append(deriv)
            else:
                ratio_derivatives.append(0)
        
        # Pad the beginning to match sample count
        ratio_derivatives = [0] * self.smoothing_window + ratio_derivatives
        
        return gear_ratios, ratio_derivatives
    
    def _calculate_smoothed_derivative(self, values: List[float], index: int) -> float:
        """Calculate smoothed derivative using sliding window"""
        if index < self.smoothing_window or index >= len(values) - self.smoothing_window:
            return 0
        
        # Linear regression over window
        window_size = self.smoothing_window
        x = np.arange(-window_size, window_size + 1)
        y = values[index - window_size:index + window_size + 1]
        
        # Calculate slope (derivative)
        n = len(x)
        sum_x = np.sum(x)
        sum_y = np.sum(y)
        sum_xy = np.sum(x * y)
        sum_x2 = np.sum(x * x)
        
        denominator = n * sum_x2 - sum_x ** 2
        if denominator != 0:
            slope = (n * sum_xy - sum_x * sum_y) / denominator
        else:
            slope = 0
        
        return slope
    
    def _find_shift_events(self, samples: List[TelemetrySample], gear_ratios: List[float], 
                          ratio_derivatives: List[float]) -> List[ShiftEvent]:
        """Find shift events based on ratio change rate"""
        shift_events = []
        in_shift = False
        shift_start = 0
        max_change_rate = 0
        ratio_before = 0
        
        for i, (sample, ratio, deriv) in enumerate(zip(samples, gear_ratios, ratio_derivatives)):
            # Check for shift start
            if not in_shift and abs(deriv) > self.ratio_change_threshold:
                # Verify throttle is high and speed is smooth
                if sample.throttle_position >= self.throttle_threshold:
                    in_shift = True
                    shift_start = sample.timestamp
                    max_change_rate = abs(deriv)
                    ratio_before = gear_ratios[i-1] if i > 0 else ratio
            
            # Track maximum change rate during shift
            elif in_shift:
                max_change_rate = max(max_change_rate, abs(deriv))
            
            # Check for shift end
            elif in_shift and abs(deriv) < self.ratio_change_threshold * 0.3:
                # Shift has ended
                shift_end = sample.timestamp
                ratio_after = gear_ratios[i] if i < len(gear_ratios) else ratio_before
                
                # Determine shift type
                if ratio_after < ratio_before * 0.8:  # Upshift (ratio decreases)
                    shift_type = "UP"
                elif ratio_after > ratio_before * 1.2:  # Downshift (ratio increases)
                    shift_type = "DOWN"
                else:
                    shift_type = "UNKNOWN"
                
                # Create shift event
                shift_event = ShiftEvent(
                    timestamp_start=shift_start,
                    timestamp_end=shift_end,
                    timestamp_peak=shift_start + (shift_end - shift_start) / 2,
                    gear_ratio_before=ratio_before,
                    gear_ratio_after=ratio_after,
                    max_change_rate=max_change_rate,
                    shift_type=shift_type,
                    confidence=min(1.0, max_change_rate / self.ratio_change_threshold)
                )
                
                shift_events.append(shift_event)
                in_shift = False
        
        return shift_events
    
    def _create_segments(self, samples: List[TelemetrySample], shift_events: List[ShiftEvent], 
                        gear_ratios: List[float]) -> List[DynoSegment]:
        """Create dyno segments between shift events"""
        segments = []
        
        if not shift_events:
            # No shifts detected, create single segment
            if samples:
                segments.append(DynoSegment(
                    start_index=0,
                    end_index=len(samples) - 1,
                    start_time=samples[0].timestamp,
                    end_time=samples[-1].timestamp,
                    gear_ratio=np.median(gear_ratios) if gear_ratios else 0,
                    is_valid=True
                ))
            return segments
        
        # Create segments between shifts
        start_idx = 0
        start_time = samples[0].timestamp if samples else 0
        
        for shift in shift_events:
            # Find index of shift start
            shift_idx = next((i for i, s in enumerate(samples) 
                            if abs(s.timestamp - shift.timestamp_start) < 0.1), -1)
            
            if shift_idx > start_idx:
                # Create segment before shift
                segment_samples = samples[start_idx:shift_idx]
                segment_ratios = gear_ratios[start_idx:shift_idx]
                
                # Validate segment
                is_valid, reason = self._validate_segment(segment_samples, segment_ratios)
                
                segment = DynoSegment(
                    start_index=start_idx,
                    end_index=shift_idx - 1,
                    start_time=start_time,
                    end_time=shift.timestamp_start - self.guard_window,
                    gear_ratio=np.median(segment_ratios) if segment_ratios else 0,
                    is_valid=is_valid,
                    rejection_reason=reason if not is_valid else None
                )
                
                segments.append(segment)
            
            # Skip guard window
            start_idx = next((i for i, s in enumerate(samples) 
                            if s.timestamp > shift.timestamp_end + self.guard_window), len(samples))
            start_time = shift.timestamp_end + self.guard_window
        
        # Create final segment after last shift
        if start_idx < len(samples):
            segment_samples = samples[start_idx:]
            segment_ratios = gear_ratios[start_idx:]
            
            # Validate segment
            is_valid, reason = self._validate_segment(segment_samples, segment_ratios)
            
            segment = DynoSegment(
                start_index=start_idx,
                end_index=len(samples) - 1,
                start_time=start_time,
                end_time=samples[-1].timestamp,
                gear_ratio=np.median(segment_ratios) if segment_ratios else 0,
                is_valid=is_valid,
                rejection_reason=reason if not is_valid else None
            )
            
            # Check minimum duration
            if segment.end_time - segment.start_time >= self.min_segment_duration:
                segments.append(segment)
        
        return segments
    
    def _validate_segment(self, samples: List[TelemetrySample], gear_ratios: List[float]) -> Tuple[bool, Optional[str]]:
        """Validate a dyno segment"""
        if not samples or not gear_ratios:
            return False, "No data"
        
        # Check duration
        duration = samples[-1].timestamp - samples[0].timestamp
        if duration < self.min_segment_duration:
            return False, f"Too short: {duration:.2f}s < {self.min_segment_duration}s"
        
        # Check throttle
        avg_throttle = np.mean([s.throttle_position for s in samples])
        if avg_throttle < self.throttle_threshold:
            return False, f"Low throttle: {avg_throttle:.1f}% < {self.throttle_threshold}%"
        
        # Check gear ratio stability
        ratio_variance = np.var(gear_ratios)
        if ratio_variance > 0.1:  # Too unstable
            return False, f"Unstable gear ratio: var={ratio_variance:.3f}"
        
        # Check for wheelspin
        if self._detect_wheelspin(samples, gear_ratios):
            return False, "Wheelspin detected"
        
        return True, None
    
    def _detect_wheelspin(self, samples: List[TelemetrySample], gear_ratios: List[float]) -> bool:
        """Detect wheelspin from unstable ratio during high throttle"""
        if len(samples) < 5:
            return False
        
        # Check for high throttle with unstable ratio
        high_throttle_samples = [s for s in samples if s.throttle_position > 90]
        
        if len(high_throttle_samples) > len(samples) * 0.5:
            ratio_variance = np.var(gear_ratios)
            if ratio_variance > 0.05:  # Significant variance during WOT
                return True
        
        return False
