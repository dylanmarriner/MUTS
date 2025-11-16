"""
Real-time Tuning and Monitoring System
Live parameter adjustment and data logging for Mazdaspeed 3
"""

import threading
import time
import json
import csv
import struct
from datetime import datetime
from collections import deque
import matplotlib.pyplot as plt
import numpy as np

class RealTimeMonitor:
    """
    Real-time ECU parameter monitoring and visualization
    Provides live data display and logging capabilities
    """
    
    def __init__(self, ecu):
        self.ecu = ecu
        self.monitoring = False
        self.logging = False
        self.update_interval = 0.1  # 100ms
        self.data_buffer = deque(maxlen=1000)  # Store last 1000 samples
        self.parameters = [
            'ENGINE_RPM', 'MANIFOLD_PRESSURE', 'THROTTLE_POSITION',
            'IGNITION_TIMING', 'AFR', 'INTAKE_TEMP', 'COOLANT_TEMP',
            'FUEL_TRIM_SHORT', 'KNOCK_RETARD', 'WASTEGATE_DUTY'
        ]
        
    def start_monitoring(self):
        """Start real-time monitoring thread"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        print("[+] Real-time monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring thread"""
        self.monitoring = False
        if self.logging:
            self.stop_logging()
        print("[+] Real-time monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            sample = {
                'timestamp': datetime.now(),
                'data': {}
            }
            
            # Read all parameters
            for param in self.parameters:
                value = self.ecu.read_realtime_parameter(param)
                if value is not None:
                    sample['data'][param] = value
            
            # Add to buffer
            self.data_buffer.append(sample)
            
            # Display current values
            self._display_current_values(sample)
            
            time.sleep(self.update_interval)
    
    def _display_current_values(self, sample):
        """Display current parameter values in formatted output"""
        if not sample['data']:
            return
            
        print("\033[2J\033[H")  # Clear screen
        print("=== Mazdaspeed 3 Real-time Monitor ===")
        print(f"Time: {sample['timestamp'].strftime('%H:%M:%S.%f')[:-3]}")
        print("-" * 40)
        
        # Group parameters for better display
        groups = {
            'Engine': ['ENGINE_RPM', 'MANIFOLD_PRESSURE', 'THROTTLE_POSITION'],
            'Ignition': ['IGNITION_TIMING', 'KNOCK_RETARD'],
            'Fuel': ['AFR', 'FUEL_TRIM_SHORT'],
            'Temps': ['INTAKE_TEMP', 'COOLANT_TEMP'],
            'Boost': ['WASTEGATE_DUTY']
        }
        
        for group_name, params in groups.items():
            print(f"\n{group_name}:")
            for param in params:
                if param in sample['data']:
                    value = sample['data'][param]
                    unit = self._get_parameter_unit(param)
                    print(f"  {param.replace('_', ' ').title():20} {value:8.2f} {unit}")
    
    def _get_parameter_unit(self, param):
        """Get display unit for parameter"""
        units = {
            'ENGINE_RPM': 'RPM',
            'MANIFOLD_PRESSURE': 'psi',
            'THROTTLE_POSITION': '%',
            'IGNITION_TIMING': '°',
            'AFR': 'AFR',
            'INTAKE_TEMP': '°C',
            'COOLANT_TEMP': '°C',
            'FUEL_TRIM_SHORT': '%',
            'KNOCK_RETARD': '°',
            'WASTEGATE_DUTY': '%'
        }
        return units.get(param, '')
    
    def start_logging(self, filename=None):
        """Start data logging to file"""
        if not filename:
            filename = f"ms3_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        self.log_file = filename
        self.logging = True
        print(f"[+] Logging started: {filename}")
    
    def stop_logging(self):
        """Stop data logging"""
        self.logging = False
        print("[+] Logging stopped")
    
    def export_log(self, filename=None):
        """Export logged data to CSV"""
        if not filename:
            filename = f"ms3_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        try:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Write header
                header = ['Timestamp'] + self.parameters
                writer.writerow(header)
                
                # Write data
                for sample in self.data_buffer:
                    row = [sample['timestamp'].isoformat()]
                    for param in self.parameters:
                        row.append(sample['data'].get(param, ''))
                    writer.writerow(row)
            
            print(f"[+] Data exported to {filename}")
            return True
            
        except Exception as e:
            print(f"[-] Export failed: {e}")
            return False
    
    def plot_parameters(self, params=None, time_window=60):
        """Plot parameter data over time"""
        if not params:
            params = ['ENGINE_RPM', 'MANIFOLD_PRESSURE', 'IGNITION_TIMING']
        
        # Extract data for plotting
        timestamps = []
        data_series = {param: [] for param in params}
        
        for sample in list(self.data_buffer)[-int(time_window/self.update_interval):]:
            timestamps.append(sample['timestamp'])
            for param in params:
                data_series[param].append(sample['data'].get(param, 0))
        
        if not timestamps:
            print("No data to plot")
            return
        
        # Create plot
        fig, axes = plt.subplots(len(params), 1, figsize=(12, 8))
        if len(params) == 1:
            axes = [axes]
        
        time_deltas = [(ts - timestamps[0]).total_seconds() for ts in timestamps]
        
        for i, param in enumerate(params):
            axes[i].plot(time_deltas, data_series[param], linewidth=2)
            axes[i].set_ylabel(f'{param.replace("_", " ").title()}')
            axes[i].grid(True, alpha=0.3)
            
            # Add unit to y-axis label
            unit = self._get_parameter_unit(param)
            if unit:
                axes[i].set_ylabel(f'{param.replace("_", " ").title()} ({unit})')
        
        axes[-1].set_xlabel('Time (seconds)')
        plt.tight_layout()
        plt.show()

class LiveTuner:
    """
    Live tuning parameter adjustment
    Allows real-time modification of ECU parameters while driving
    """
    
    def __init__(self, ecu):
        self.ecu = ecu
        self.active_adjustments = {}
        self.tuning_maps = {}
        self.safety_limits = {
            'BOOST_TARGET': 25.0,  # psi
            'IGNITION_TIMING': 25.0,  # degrees
            'FUEL_BASE': 1.5,  # multiplier
            'REV_LIMITER': 7500  # RPM
        }
    
    def adjust_parameter(self, param_name: str, adjustment: float, immediate: bool = True) -> bool:
        """
        Adjust tuning parameter with safety checks
        """
        # Safety validation
        if not self._validate_adjustment(param_name, adjustment):
            return False
        
        if immediate:
            # Real-time RAM adjustment
            return self._adjust_realtime_parameter(param_name, adjustment)
        else:
            # Calibration table adjustment
            return self._adjust_calibration_parameter(param_name, adjustment)
    
    def _validate_adjustment(self, param_name: str, adjustment: float) -> bool:
        """Validate adjustment against safety limits"""
        current_value = self.ecu.read_realtime_parameter(param_name)
        if current_value is None:
            return False
        
        new_value = current_value + adjustment
        
        if param_name in self.safety_limits:
            limit = self.safety_limits[param_name]
            if abs(new_value) > limit:
                print(f"Safety limit exceeded: {param_name} > {limit}")
                return False
        
        return True
    
    def _adjust_realtime_parameter(self, param_name: str, adjustment: float) -> bool:
        """Adjust parameter in ECU RAM (immediate effect)"""
        current_value = self.ecu.read_realtime_parameter(param_name)
        if current_value is None:
            return False
        
        # Convert to raw ECU value
        raw_current = self._engineering_to_raw(param_name, current_value)
        raw_new = self._engineering_to_raw(param_name, current_value + adjustment)
        
        # Calculate raw adjustment
        raw_adjustment = raw_new - raw_current
        
        # Write to ECU RAM
        address = self.ecu.REALTIME_PARAMS[param_name]
        raw_bytes = struct.pack('>H', int(raw_new))
        
        if self.ecu.can.write_memory(address, raw_bytes):
            self.active_adjustments[param_name] = adjustment
            print(f"Adjusted {param_name}: {current_value:.2f} -> {current_value + adjustment:.2f}")
            return True
        
        return False
    
    def _adjust_calibration_parameter(self, param_name: str, adjustment: float) -> bool:
        """Adjust parameter in calibration tables (permanent)"""
        # This would modify the actual calibration tables
        # Implementation depends on specific table structure
        print(f"Calibration adjustment for {param_name}: {adjustment}")
        # Placeholder - actual implementation would modify calibration tables
        return True
    
    def _engineering_to_raw(self, param: str, value: float) -> int:
        """Convert engineering units to raw ECU values"""
        conversions = {
            'ENGINE_RPM': lambda x: int(x / 0.25),
            'MANIFOLD_PRESSURE': lambda x: int((x + 1) / 0.01),
            'THROTTLE_POSITION': lambda x: int(x / 0.001),
            'IGNITION_TIMING': lambda x: int((x + 64) * 10),
            'AFR': lambda x: int(x * 100),
            'FUEL_TRIM_SHORT': lambda x: int((x + 1) * 1000),
            'KNOCK_RETARD': lambda x: int(x * 10),
            'WASTEGATE_DUTY': lambda x: int(x * 10)
        }
        return conversions.get(param, lambda x: int(x))(value)
    
    def create_boost_map(self, target_boost: float, rpm_range: tuple = (2000, 6500)) -> bool:
        """Create custom boost map targeting specific boost level"""
        try:
            # Load boost tables
            boost_target_data = self.ecu.read_calibration_table('BOOST_TARGET')
            wg_duty_data = self.ecu.read_calibration_table('BOOST_WG_DUTY')
            
            if not boost_target_data or not wg_duty_data:
                return False
            
            # Parse table data
            boost_table = self._parse_boost_table(boost_target_data)
            wg_table = self._parse_boost_table(wg_duty_data)
            
            # Modify tables for target boost
            rpm_min, rpm_max = rpm_range
            self._modify_boost_tables(boost_table, wg_table, target_boost, rpm_min, rpm_max)
            
            # Convert back to bytes and write
            new_boost_data = self._serialize_boost_table(boost_table)
            new_wg_data = self._serialize_boost_table(wg_table)
            
            if (self.ecu.write_calibration_table('BOOST_TARGET', new_boost_data) and
                self.ecu.write_calibration_table('BOOST_WG_DUTY', new_wg_data)):
                self.tuning_maps['BOOST_MAP'] = {
                    'target': target_boost,
                    'rpm_range': rpm_range,
                    'timestamp': datetime.now()
                }
                return True
        
        except Exception as e:
            print(f"Boost map creation failed: {e}")
        
        return False
    
    def _parse_boost_table(self, data: bytes) -> np.ndarray:
        """Parse boost table data to numpy array"""
        return np.frombuffer(data, dtype=np.float32).reshape(8, 8)
    
    def _serialize_boost_table(self, table: np.ndarray) -> bytes:
        """Serialize numpy array back to bytes"""
        return table.astype(np.float32).tobytes()
    
    def _modify_boost_tables(self, boost_table, wg_table, target_boost, rpm_min, rpm_max):
        """Modify boost control tables for target boost"""
        # Simple boost targeting algorithm
        # In practice, this would be much more sophisticated
        
        for i in range(boost_table.shape[0]):  # RPM axis
            for j in range(boost_table.shape[1]):  # Load axis
                current_boost = boost_table[i, j]
                
                # Only modify within target RPM range
                if rpm_min <= (i * 1000) <= rpm_max:
                    # Increase boost target
                    if current_boost < target_boost:
                        boost_table[i, j] = target_boost
                        # Increase WG duty to achieve target
                        wg_table[i, j] = min(wg_table[i, j] * 0.8, 95.0)  # Reduce WG duty
    
    def reset_all_adjustments(self):
        """Reset all active adjustments to default"""
        for param_name, adjustment in self.active_adjustments.items():
            self.adjust_parameter(param_name, -adjustment)
        
        self.active_adjustments.clear()
        print("[+] All adjustments reset")
    
    def save_tuning_profile(self, filename: str):
        """Save current tuning adjustments to profile"""
        profile = {
            'adjustments': self.active_adjustments,
            'tuning_maps': self.tuning_maps,
            'timestamp': datetime.now().isoformat(),
            'ecu_info': self.ecu.can.read_ecu_identification()
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(profile, f, indent=2)
            print(f"[+] Tuning profile saved: {filename}")
            return True
        except Exception as e:
            print(f"[-] Failed to save profile: {e}")
            return False
    
    def load_tuning_profile(self, filename: str) -> bool:
        """Load tuning profile from file"""
        try:
            with open(filename, 'r') as f:
                profile = json.load(f)
            
            # Apply adjustments
            for param_name, adjustment in profile.get('adjustments', {}).items():
                self.adjust_parameter(param_name, adjustment)
            
            self.tuning_maps = profile.get('tuning_maps', {})
            print(f"[+] Tuning profile loaded: {filename}")
            return True
            
        except Exception as e:
            print(f"[-] Failed to load profile: {e}")
            return False