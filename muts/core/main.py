"""
MAZDASPEED 3 MASTER TUNING APPLICATION
Main entry point for the complete tuning and diagnostic system
"""

import time
import threading
import logging
from datetime import datetime
from typing import Dict, List, Optional

from diagnostic_module import DiagnosticMessage, MazdaDiagnosticProtocol
from muts.comms.can_interface import Mazdaspeed3CANInterface
from muts.database import Mazdaspeed3Database
from muts.security import MazdaECUType, MazdaSeedKeyDatabase
from muts.services.ai_tuner import AITuningSystem
from muts.services.dealer_service import MazdaDealerSecurity
from muts.services.performance_features import AdvancedPerformanceManager
from muts.services.physics_engine import TurbochargerPhysics, EngineThermodynamics, PerformanceCalculator
from muts.models.turbo_models import TurboSystemManager
from muts.utils.calculations import AdvancedCalculations, TuningSecrets
from muts.utils.security import SecurityManager
from muts.config.mazdaspeed3_config import *

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mazdaspeed3_tuner.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class Mazdaspeed3Tuner:
    """
    COMPLETE MAZDASPEED 3 TUNING MASTER CONTROLLER
    Integrates all systems for real-time tuning and diagnostics
    """

    def __init__(self):
        # Initialize all subsystems
        self.database = Mazdaspeed3Database()
        self.factory_calibration = None
        self.encrypted_calibration_data = None
        self.calibration_signature = None
        self.vehicle_vin = "JM1BK123456789012"
        self.security_manager = SecurityManager()
        self.seed_key_database = MazdaSeedKeyDatabase()
        self.can_interface = Mazdaspeed3CANInterface()
        self.can_connected = False
        self.diagnostic_protocol = MazdaDiagnosticProtocol()
        self.ai_tuner = AITuningSystem()
        self.dealer_security = MazdaDealerSecurity()
        self.performance_manager = AdvancedPerformanceManager()
        self.turbo_manager = TurboSystemManager()
        self.calculations = AdvancedCalculations()
        self.tuning_secrets = TuningSecrets()

        # Physics engines
        self.turbo_physics = TurbochargerPhysics()
        self.engine_thermo = EngineThermodynamics()
        self.performance_calc = PerformanceCalculator()

        # Real-time data
        self.current_sensor_data = {}
        self.tuning_parameters = {}
        self.system_status = {}

        # Control flags
        self.tuning_active = False
        self.data_logging = True
        self.safety_override = False

        # Threading
        self.data_thread = None
        self.tuning_thread = None
        self.shutdown_flag = threading.Event()

        # Initialize system
        self._initialize_system()

    def _initialize_system(self):
        """Initialize all systems and load calibration data"""
        logger.info("Initializing Mazdaspeed 3 Tuning System...")

        try:
            self._initialize_database()
            self._initialize_security_helpers()
            self._connect_to_can_bus()

            # Initialize AI models
            self.ai_tuner.load_models('ai_models')
            logger.info("AI tuning models loaded")

            # Test dealer security access
            security_status = self.dealer_security.perform_security_access('ecu')
            logger.info(f"Dealer security access: {security_status}")

            # Set initial performance mode
            self.performance_manager.set_performance_mode('street')

            self.system_status = {
                'initialized': True,
                'database_connected': bool(self.factory_calibration),
                'ai_models_loaded': True,
                'security_access': True,
                'calibration_signature': self.calibration_signature,
                'can_connected': self.can_connected,
                'diagnostic_session_active': self.diagnostic_protocol.is_connected,
                'startup_time': datetime.now().isoformat()
            }

            logger.info("Mazdaspeed 3 Tuning System initialized successfully")

        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            self.system_status['initialized'] = False
            raise

    def _initialize_database(self):
        """Load factory calibration records from the database."""
        self.factory_calibration = self.database.get_factory_calibration()
        if self.factory_calibration:
            logger.info(f"Loaded factory calibration {self.factory_calibration.calibration_id}")
        else:
            logger.warning("Factory calibration not found, operating in simulation mode")

    def _serialize_calibration(self, calibration) -> Dict[str, str]:
        """Serialize calibration record to a simple dictionary for logging/security."""
        return {
            'calibration_id': calibration.calibration_id,
            'vehicle_model': calibration.vehicle_model,
            'ecu_hardware': calibration.ecu_hardware,
            'description': calibration.description or ''
        }

    def _initialize_security_helpers(self):
        """Encrypt factory calibration data and generate vehicle signature."""
        if not self.factory_calibration:
            return

        try:
            payload = self._serialize_calibration(self.factory_calibration)
            self.encrypted_calibration_data = self.security_manager.encrypt_calibration_data(payload)
            self.calibration_signature = self.security_manager.generate_vehicle_signature(
                self.vehicle_vin, payload['calibration_id']
            )
            logger.info("Security payloads initialized for calibration data")
        except Exception as exc:
            logger.warning(f"Failed to initialize security helpers: {exc}")

    def _connect_to_can_bus(self) -> bool:
        """Attempt to connect to the CAN bus and start live data streaming."""
        try:
            if self.can_interface.connect():
                self.can_interface.start_receiving()
                self.can_connected = True
                logger.info("CAN interface connected and receiving data")
                return True
        except Exception as exc:
            logger.warning(f"CAN bus connection unavailable: {exc}")

        self.can_connected = False
        return False

    def _disconnect_can_bus(self):
        """Disconnect from the CAN interface cleanly."""
        if self.can_connected:
            self.can_interface.disconnect()
            self.can_connected = False
            logger.info("CAN interface disconnected")

    def _get_live_can_data(self) -> Dict[str, float]:
        """Fetch the latest live CAN data snapshot."""
        if not self.can_connected:
            return {}

        return self.can_interface.get_live_data()

    def _simulate_sensor_data(self) -> Dict[str, float]:
        """Return simulator sensor data when live CAN data is unavailable."""
        return {
            'timestamp': time.time(),
            'engine_rpm': 3200,
            'vehicle_speed': 45.2,
            'throttle_position': 65.8,
            'boost_psi': 16.2,
            'manifold_pressure': 215.4,
            'mass_airflow': 0.085,
            'intake_temp': 32.1,
            'coolant_temp': 94.2,
            'exhaust_temp': 785.4,
            'ignition_timing': 14.8,
            'afr': 11.8,
            'knock_retard': -1.2,
            'fuel_trim_long': 2.1,
            'fuel_trim_short': -0.8,
            'vvt_intake_angle': 18.5,
            'vvt_exhaust_angle': 8.2,
            'clutch_position': 100.0,
            'current_gear': 3,
            'wheel_speeds': [45.2, 45.1, 44.8, 44.9],
            'battery_voltage': 13.8,
            'injector_duty': 42.5,
            'wastegate_duty': 58.3,
            'turbo_rpm': 85000
        }

    def _build_sensor_data_from_live_data(self, live_data: Dict[str, float]) -> Dict[str, float]:
        """Merge live CAN readings into the tuning sensor template."""
        sensor_data = self._simulate_sensor_data()
        sensor_data.update(live_data)
        sensor_data['timestamp'] = time.time()

        if sensor_data.get('boost_psi') is not None:
            sensor_data['manifold_pressure'] = (
                max(1.0, sensor_data['boost_psi']) * 6.89476 + 101.325
            )

        for field in ['knock_retard', 'fuel_trim_long', 'fuel_trim_short',
                      'vvt_intake_angle', 'vvt_exhaust_angle', 'exhaust_temp',
                      'turbo_rpm']:
            if field in live_data:
                sensor_data[field] = live_data[field]

        return sensor_data

    def start_diagnostic_session(self) -> bool:
        """Establish a diagnostic session with the vehicle."""
        connected = self.diagnostic_protocol.connect_to_vehicle()
        if connected:
            logger.info("Diagnostic session established")
        return connected

    def stop_diagnostic_session(self):
        """Close the diagnostic protocol session."""
        self.diagnostic_protocol.disconnect()
        logger.info("Diagnostic session terminated")

    def read_diagnostic_identifier(self, identifier: int) -> Optional[DiagnosticMessage]:
        """Read a single data identifier through the diagnostic protocol."""
        if not self.diagnostic_protocol.is_connected:
            if not self.diagnostic_protocol.connect_to_vehicle():
                return None

        message = DiagnosticMessage(
            target_address=self.diagnostic_protocol.ECU_ADDRESSES['ENGINE_ECU'],
            source_address=0x7DF,
            service_id=0x22,
            sub_function=0x00,
            data=identifier.to_bytes(2, 'big')
        )

        return self.diagnostic_protocol.send_diagnostic_message(message)

    def fetch_dtc_list(self) -> List[Dict]:
        """Read current diagnostic trouble codes via the CAN interface."""
        if not self.can_connected:
            self._connect_to_can_bus()

        if not self.can_connected:
            return []

        return self.can_interface.read_dtcs()

    def derive_security_key(self, seed: bytes, security_level: int = 1) -> Optional[bytes]:
        """Derive a Mazda security key using the seed/key helper database."""
        ecu_info = self.seed_key_database.ecu_database.get(MazdaECUType.ENGINE_ECU)
        if not ecu_info:
            return None

        seed_length = ecu_info['seed_length']
        truncated_seed = seed[:seed_length].ljust(seed_length, b'\x00')

        return self.seed_key_database.calculate_key(
            truncated_seed,
            ecu_info['algorithm'],
            security_level=security_level
        )

    def start_real_time_tuning(self):
        """Start real-time tuning and data acquisition"""
        if self.tuning_active:
            logger.warning("Tuning already active")
            return

        self.tuning_active = True
        self.shutdown_flag.clear()

        # Start data acquisition thread
        self.data_thread = threading.Thread(target=self._data_acquisition_loop)
        self.data_thread.daemon = True
        self.data_thread.start()

        # Start tuning optimization thread
        self.tuning_thread = threading.Thread(target=self._tuning_optimization_loop)
        self.tuning_thread.daemon = True
        self.tuning_thread.start()

        logger.info("Real-time tuning started")

    def stop_real_time_tuning(self):
        """Stop real-time tuning"""
        self.tuning_active = False
        self.shutdown_flag.set()

        if self.data_thread:
            self.data_thread.join(timeout=5.0)
        if self.tuning_thread:
            self.tuning_thread.join(timeout=5.0)

        logger.info("Real-time tuning stopped")
        self._disconnect_can_bus()

    def _data_acquisition_loop(self):
        """Main data acquisition loop - reads sensor data in real-time"""
        logger.info("Starting data acquisition loop")

        while not self.shutdown_flag.is_set() and self.tuning_active:
            try:
                # Read current sensor data (in real implementation, this would read from CAN bus)
                sensor_data = self._read_sensor_data()

                # Update current sensor data
                self.current_sensor_data = sensor_data

                # Log data if enabled
                if self.data_logging:
                    self._log_sensor_data(sensor_data)

                # Process data through physics models
                self._process_sensor_data(sensor_data)

                # Brief sleep to control loop frequency (100Hz)
                time.sleep(0.01)

            except Exception as e:
                logger.error(f"Data acquisition error: {e}")
                time.sleep(0.1)  # Longer sleep on error

    def _read_sensor_data(self) -> dict:
        """
        Read current sensor data from vehicle systems
        In real implementation, this would interface with CAN bus and OBD-II
        """
        live_data = self._get_live_can_data()
        if live_data:
            return self._build_sensor_data_from_live_data(live_data)

        return self._simulate_sensor_data()

    def _log_sensor_data(self, sensor_data: dict):
        """Log sensor data for analysis and machine learning"""
        # In real implementation, this would write to database or file
        pass

    def _process_sensor_data(self, sensor_data: dict):
        """Process sensor data through physics models and calculations"""
        try:
            # Calculate derived parameters
            engine_load = sensor_data['mass_airflow'] / 0.12  # Simplified load calculation
            volumetric_efficiency = self.calculations.calculate_volumetric_efficiency(
                sensor_data['engine_rpm'], 0.3, 0.05, 0.035, 240  # Example parameters
            )

            # Update sensor data with calculated values
            sensor_data['engine_load'] = engine_load
            sensor_data['volumetric_efficiency'] = volumetric_efficiency

            # Calculate performance metrics
            indicated_torque = self.engine_thermo.calculate_indicated_power(
                sensor_data['mass_airflow'], sensor_data['afr'],
                sensor_data['ignition_timing'], ENGINE_SPECS['compression_ratio']
            )

            brake_torque = self.engine_thermo.calculate_brake_torque(
                indicated_torque, sensor_data['engine_rpm']
            )

            horsepower = self.calculations.calculate_brake_horsepower(
                brake_torque, sensor_data['engine_rpm']
            )

            # Update performance data
            sensor_data.update({
                'indicated_torque_nm': indicated_torque,
                'brake_torque_nm': brake_torque,
                'horsepower': horsepower
            })

        except Exception as e:
            logger.error(f"Sensor data processing error: {e}")

    def _tuning_optimization_loop(self):
        """Main tuning optimization loop - runs AI tuning in real-time"""
        logger.info("Starting tuning optimization loop")

        while not self.shutdown_flag.is_set() and self.tuning_active:
            try:
                # Check if we have valid sensor data
                if not self.current_sensor_data:
                    time.sleep(0.02)
                    continue

                # Get performance features parameters
                performance_params = self.performance_manager.calculate_integrated_performance_parameters(
                    self.current_sensor_data
                )

                # Run AI tuning optimization
                ai_adjustments = self.ai_tuner.real_time_optimization(self.current_sensor_data)

                # Apply tuning secrets
                secret_adjustments = self._apply_tuning_secrets(self.current_sensor_data)

                # Combine all adjustments
                combined_adjustments = self._combine_tuning_adjustments(
                    ai_adjustments, performance_params, secret_adjustments
                )

                # Apply safety limits
                safe_adjustments = self._apply_safety_limits(combined_adjustments)

                # Update tuning parameters
                self.tuning_parameters = safe_adjustments

                # Apply tuning to vehicle (in real implementation, this would write to ECU)
                self._apply_tuning_parameters(safe_adjustments)

                # Update turbo system model
                turbo_update = self.turbo_manager.update_turbo_system(
                    self.current_sensor_data['engine_rpm'],
                    self.current_sensor_data['throttle_position'],
                    self.current_sensor_data['mass_airflow'],
                    self.current_sensor_data['exhaust_temp'],
                    self.current_sensor_data['manifold_pressure'] / 101.325,  # Pressure ratio
                    0.01  # Time step
                )

                # Update system status
                self._update_system_status(performance_params, safe_adjustments, turbo_update)

                # Brief sleep to control optimization frequency (50Hz)
                time.sleep(0.02)

            except Exception as e:
                logger.error(f"Tuning optimization error: {e}")
                time.sleep(0.1)  # Longer sleep on error

    def _apply_tuning_secrets(self, sensor_data: dict) -> dict:
        """Apply proprietary tuning secrets based on current conditions"""
        adjustments = {}

        try:
            # Faster spool technique
            spool_adjustments = self.tuning_secrets.apply_tuning_secret('faster_spool_lower_psi', {
                'rpm': sensor_data['engine_rpm'],
                'target_boost': 18.0,
                'current_boost': sensor_data['boost_psi'],
                'throttle_position': sensor_data['throttle_position']
            })
            adjustments.update(spool_adjustments)

            # VVT torque optimization
            vvt_adjustments = self.tuning_secrets.apply_tuning_secret('vvt_torque_optimization', {
                'rpm': sensor_data['engine_rpm'],
                'load': sensor_data.get('engine_load', 0.8),
                'throttle_position': sensor_data['throttle_position']
            })
            adjustments.update(vvt_adjustments)

            # Boost taper optimization
            boost_adjustments = self.tuning_secrets.apply_tuning_secret('boost_taper_optimization', {
                'rpm': sensor_data['engine_rpm'],
                'current_boost': sensor_data['boost_psi'],
                'target_boost': 18.0,
                'airflow': sensor_data['mass_airflow']
            })
            adjustments.update(boost_adjustments)

        except Exception as e:
            logger.error(f"Tuning secrets application error: {e}")

        return adjustments

    def _combine_tuning_adjustments(self, ai_adjustments: dict, performance_params: dict,
                                  secret_adjustments: dict) -> dict:
        """Intelligently combine all tuning adjustments with priority handling"""
        combined = {}

        # Start with performance features (highest priority for safety)
        if performance_params.get('ignition_retard_final', 0) < 0:
            combined['ignition_timing'] = performance_params['ignition_retard_final']

        if performance_params.get('fuel_adjustment_final', 0) != 0:
            combined['fuel_enrichment'] = performance_params['fuel_adjustment_final']

        if performance_params.get('boost_target_final', 0) != 0:
            combined['boost_target'] = performance_params['boost_target_final']

        # Add AI adjustments with moderate weight
        for key, value in ai_adjustments.items():
            if key in combined:
                # Average with existing value (AI gets 40% weight)
                combined[key] = 0.6 * combined[key] + 0.4 * value
            else:
                combined[key] = value * 0.6  # Reduced weight for AI-only adjustments

        # Add secret adjustments with situational weight
        for key, value in secret_adjustments.items():
            if key in combined:
                # Secrets get higher weight in their domain
                if 'spool' in key or 'boost' in key:
                    combined[key] = 0.3 * combined[key] + 0.7 * value
                else:
                    combined[key] = 0.5 * combined[key] + 0.5 * value
            else:
                combined[key] = value

        return combined

    def _apply_safety_limits(self, adjustments: dict) -> dict:
        """Apply all safety limits to tuning adjustments"""
        safe_adjustments = adjustments.copy()

        # Ignition timing limits
        if 'ignition_timing' in safe_adjustments:
            current_timing = self.current_sensor_data.get('ignition_timing', 15.0)
            new_timing = current_timing + safe_adjustments['ignition_timing']
            max_timing = SAFETY_LIMITS['max_ignition_timing']

            if new_timing > max_timing:
                safe_adjustments['ignition_timing'] = max_timing - current_timing

        # Boost limits
        if 'boost_target' in safe_adjustments:
            safe_adjustments['boost_target'] = min(
                safe_adjustments['boost_target'],
                SAFETY_LIMITS['max_boost_psi']
            )

        # AFR limits
        if 'target_afr' in safe_adjustments:
            safe_adjustments['target_afr'] = max(
                SAFETY_LIMITS['min_afr'],
                min(safe_adjustments['target_afr'], SAFETY_LIMITS['max_afr'])
            )

        # Temperature-based adjustments
        intake_temp = self.current_sensor_data.get('intake_temp', 25.0)
        coolant_temp = self.current_sensor_data.get('coolant_temp', 90.0)

        if intake_temp > 40.0 and 'ignition_timing' in safe_adjustments:
            # Reduce timing advance in hot conditions
            safe_adjustments['ignition_timing'] *= 0.7

        if coolant_temp > 100.0:
            # Reduce boost and timing if coolant is hot
            if 'boost_target' in safe_adjustments:
                safe_adjustments['boost_target'] *= 0.8
            if 'ignition_timing' in safe_adjustments:
                safe_adjustments['ignition_timing'] *= 0.5

        return safe_adjustments

    def _apply_tuning_parameters(self, adjustments: dict):
        """Apply tuning parameters to vehicle systems"""
        # In real implementation, this would write to ECU via CAN bus
        # This is a simulation of the tuning application

        try:
            # Calculate wastegate duty cycle for boost control
            if 'boost_target' in adjustments:
                wgdc = self.turbo_manager.calculate_wastegate_control(
                    self.current_sensor_data['boost_psi'],
                    adjustments['boost_target'],
                    self.current_sensor_data['engine_rpm'],
                    self.current_sensor_data['throttle_position']
                )
                adjustments['wastegate_duty'] = wgdc

            # Log applied adjustments
            if adjustments:
                logger.debug(f"Applied tuning adjustments: {adjustments}")

        except Exception as e:
            logger.error(f"Tuning application error: {e}")

    def _update_system_status(self, performance_params: dict, tuning_parameters: dict,
                            turbo_update: dict):
        """Update comprehensive system status"""
        self.system_status.update({
            'last_update': datetime.now().isoformat(),
            'tuning_active': self.tuning_active,
            'performance_mode': self.performance_manager.current_mode,
            'als_active': performance_params.get('anti_lag', {}).get('als_active', False),
            'launch_active': performance_params.get('launch_control', {}).get('launch_active', False),
            'two_step_active': performance_params.get('two_step', {}).get('rev_limit_active', False),
            'safety_override': self.safety_override,
            'turbo_rpm': turbo_update.get('turbo_rpm', 0),
            'compressor_efficiency': turbo_update.get('compressor_efficiency', 0),
            'turbine_efficiency': turbo_update.get('turbine_efficiency', 0),
            'current_adjustments': tuning_parameters
        })

    def get_system_status(self) -> dict:
        """Get complete system status"""
        return {
            'system': self.system_status,
            'sensors': self.current_sensor_data,
            'tuning': self.tuning_parameters,
            'performance': self.performance_manager.current_mode
        }

    def set_performance_mode(self, mode: str):
        """Set performance mode (street, track, drag, off)"""
        try:
            self.performance_manager.set_performance_mode(mode)
            logger.info(f"Performance mode set to: {mode}")
        except Exception as e:
            logger.error(f"Failed to set performance mode: {e}")
            raise

    def execute_dealer_command(self, command: str, parameters: dict = None) -> dict:
        """Execute dealer-level diagnostic command"""
        try:
            result = self.dealer_security.execute_dealer_command(command, parameters)
            logger.info(f"Dealer command executed: {command}")
            return result
        except Exception as e:
            logger.error(f"Dealer command failed: {e}")
            raise

    def clear_adaptations(self) -> dict:
        """Clear all ECU adaptations"""
        try:
            results = self.dealer_security.clear_all_adaptations()
            logger.info("ECU adaptations cleared")
            return results
        except Exception as e:
            logger.error(f"Failed to clear adaptations: {e}")
            raise

    def save_ai_models(self):
        """Save trained AI models to disk"""
        try:
            self.ai_tuner.save_models('ai_models')
            logger.info("AI models saved successfully")
        except Exception as e:
            logger.error(f"Failed to save AI models: {e}")
            raise
