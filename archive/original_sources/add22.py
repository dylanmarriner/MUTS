#!/usr/bin/env python3
"""
COMPLETE DATA LOGGING AND TELEMETRY SYSTEM
Real-time data recording, analysis, and performance tracking
"""

import sqlite3
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class LogEntry:
    """Standardized log entry structure"""
    timestamp: float
    engine_rpm: float
    vehicle_speed: float
    throttle_position: float
    boost_psi: float
    ignition_timing: float
    afr: float
    knock_retard: float
    intake_temp: float
    coolant_temp: float
    mass_airflow: float
    vvt_intake_angle: float
    vvt_exhaust_angle: float
    fuel_trim_long: float
    fuel_trim_short: float
    calculated_torque: float
    calculated_horsepower: float
    performance_mode: str
    tuning_adjustments: Dict

class DataLogger:
    """
    COMPREHENSIVE DATA LOGGING SYSTEM FOR MAZDASPEED 3
    Records, analyzes, and stores all tuning and performance data
    """
    
    def __init__(self, db_path: str = 'mazdaspeed3_logs.db'):
        self.db_path = db_path
        self.connection = None
        self.logging_active = False
        self.log_interval = 0.1  # 10 Hz logging
        self.max_memory_entries = 10000
        
        # Real-time data buffers
        self.realtime_buffer = []
        self.buffer_lock = threading.Lock()
        
        # Statistical data
        self.session_stats = {
            'start_time': None,
            'total_entries': 0,
            'max_rpm': 0,
            'max_boost': 0,
            'max_speed': 0,
            'max_horsepower': 0
        }
        
        # Threading
        self.logging_thread = None
        self.processing_thread = None
        self.shutdown_flag = threading.Event()
        
        # Initialize database
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize SQLite database for data logging"""
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = self.connection.cursor()
            
            # Create main logging table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tuning_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    engine_rpm REAL,
                    vehicle_speed REAL,
                    throttle_position REAL,
                    boost_psi REAL,
                    ignition_timing REAL,
                    afr REAL,
                    knock_retard REAL,
                    intake_temp REAL,
                    coolant_temp REAL,
                    mass_airflow REAL,
                    vvt_intake_angle REAL,
                    vvt_exhaust_angle REAL,
                    fuel_trim_long REAL,
                    fuel_trim_short REAL,
                    calculated_torque REAL,
                    calculated_horsepower REAL,
                    performance_mode TEXT,
                    tuning_adjustments TEXT
                )
            ''')
            
            # Create session summary table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS logging_sessions (
                    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    total_entries INTEGER,
                    max_rpm REAL,
                    max_boost REAL,
                    max_speed REAL,
                    max_horsepower REAL,
                    session_duration REAL
                )
            ''')
            
            # Create performance events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_data TEXT,
                    rpm REAL,
                    speed REAL,
                    boost REAL
                )
            ''')
            
            # Create indexes for faster queries
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON tuning_logs(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_rpm ON tuning_logs(engine_rpm)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_boost ON tuning_logs(boost_psi)')
            
            self.connection.commit()
            logger.info("Data logging database initialized")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def start_logging(self):
        """Start real-time data logging"""
        if self.logging_active:
            logger.warning("Data logging already active")
            return
        
        self.logging_active = True
        self.shutdown_flag.clear()
        self.session_stats['start_time'] = datetime.now()
        self.session_stats['total_entries'] = 0
        
        # Start logging thread
        self.logging_thread = threading.Thread(target=self._logging_loop)
        self.logging_thread.daemon = True
        self.logging_thread.start()
        
        # Start processing thread
        self.processing_thread = threading.Thread(target=self._processing_loop)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        logger.info("Data logging started")
    
    def stop_logging(self):
        """Stop data logging and save session"""
        self.logging_active = False
        self.shutdown_flag.set()
        
        if self.logging_thread:
            self.logging_thread.join(timeout=5.0)
        if self.processing_thread:
            self.processing_thread.join(timeout=5.0)
        
        # Save session summary
        self._save_session_summary()
        
        # Clear buffers
        with self.buffer_lock:
            self.realtime_buffer.clear()
        
        logger.info("Data logging stopped")
    
    def _logging_loop(self):
        """Main logging loop - collects data at specified interval"""
        last_log_time = time.time()
        
        while not self.shutdown_flag.is_set() and self.logging_active:
            try:
                current_time = time.time()
                
                # Check if it's time to log
                if current_time - last_log_time >= self.log_interval:
                    # Get current data (in real implementation, this would come from CAN interface)
                    log_entry = self._collect_current_data()
                    
                    if log_entry:
                        # Add to buffer
                        with self.buffer_lock:
                            self.realtime_buffer.append(log_entry)
                            # Limit buffer size
                            if len(self.realtime_buffer) > self.max_memory_entries:
                                self.realtime_buffer = self.realtime_buffer[-self.max_memory_entries//2:]
                        
                        # Update session statistics
                        self._update_session_stats(log_entry)
                    
                    last_log_time = current_time
                
                # Brief sleep to prevent excessive CPU usage
                time.sleep(0.001)
                
            except Exception as e:
                logger.error(f"Logging loop error: {e}")
                time.sleep(0.1)
    
    def _collect_current_data(self) -> Optional[LogEntry]:
        """Collect current vehicle data for logging"""
        try:
            # In real implementation, this would read from CAN interface
            # For now, return mock data structure
            return LogEntry(
                timestamp=time.time(),
                engine_rpm=3200.0,
                vehicle_speed=45.2,
                throttle_position=65.8,
                boost_psi=16.2,
                ignition_timing=14.8,
                afr=11.8,
                knock_retard=-1.2,
                intake_temp=32.1,
                coolant_temp=94.2,
                mass_airflow=0.085,
                vvt_intake_angle=18.5,
                vvt_exhaust_angle=8.2,
                fuel_trim_long=2.1,
                fuel_trim_short=-0.8,
                calculated_torque=320.5,
                calculated_horsepower=275.3,
                performance_mode='street',
                tuning_adjustments={'ignition_timing': 0.5, 'boost_target': 0.2}
            )
            
        except Exception as e:
            logger.error(f"Data collection failed: {e}")
            return None
    
    def _processing_loop(self):
        """Process and store logged data"""
        while not self.shutdown_flag.is_set() and self.logging_active:
            try:
                # Process buffered data
                with self.buffer_lock:
                    entries_to_process = self.realtime_buffer.copy()
                    self.realtime_buffer.clear()
                
                if entries_to_process:
                    self._store_entries(entries_to_process)
                    self._detect_performance_events(entries_to_process)
                
                # Brief sleep
                time.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Processing loop error: {e}")
                time.sleep(0.1)
    
    def _store_entries(self, entries: List[LogEntry]):
        """Store log entries in database"""
        try:
            cursor = self.connection.cursor()
            
            for entry in entries:
                cursor.execute('''
                    INSERT INTO tuning_logs (
                        timestamp, engine_rpm, vehicle_speed, throttle_position,
                        boost_psi, ignition_timing, afr, knock_retard, intake_temp,
                        coolant_temp, mass_airflow, vvt_intake_angle, vvt_exhaust_angle,
                        fuel_trim_long, fuel_trim_short, calculated_torque,
                        calculated_horsepower, performance_mode, tuning_adjustments
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    entry.timestamp, entry.engine_rpm, entry.vehicle_speed,
                    entry.throttle_position, entry.boost_psi, entry.ignition_timing,
                    entry.afr, entry.knock_retard, entry.intake_temp, entry.coolant_temp,
                    entry.mass_airflow, entry.vvt_intake_angle, entry.vvt_exhaust_angle,
                    entry.fuel_trim_long, entry.fuel_trim_short, entry.calculated_torque,
                    entry.calculated_horsepower, entry.performance_mode,
                    json.dumps(entry.tuning_adjustments)
                ))
            
            self.connection.commit()
            self.session_stats['total_entries'] += len(entries)
            
        except Exception as e:
            logger.error(f"Entry storage failed: {e}")
            self.connection.rollback()
    
    def _update_session_stats(self, entry: LogEntry):
        """Update session statistics with new entry"""
        self.session_stats['max_rpm'] = max(self.session_stats['max_rpm'], entry.engine_rpm)
        self.session_stats['max_boost'] = max(self.session_stats['max_boost'], entry.boost_psi)
        self.session_stats['max_speed'] = max(self.session_stats['max_speed'], entry.vehicle_speed)
        self.session_stats['max_horsepower'] = max(self.session_stats['max_horsepower'], 
                                                 entry.calculated_horsepower)
    
    def _detect_performance_events(self, entries: List[LogEntry]):
        """Detect and record significant performance events"""
        try:
            cursor = self.connection.cursor()
            
            for entry in entries:
                # Detect boost spike
                if entry.boost_psi > 20.0:
                    self._record_event(cursor, 'boost_spike', entry)
                
                # Detect knock event
                if entry.knock_retard < -5.0:
                    self._record_event(cursor, 'knock_event', entry)
                
                # Detect high RPM
                if entry.engine_rpm > 6500:
                    self._record_event(cursor, 'high_rpm', entry)
                
                # Detect high speed
                if entry.vehicle_speed > 150.0:
                    self._record_event(cursor, 'high_speed', entry)
                
                # Detect lean condition
                if entry.afr > 13.0:
                    self._record_event(cursor, 'lean_condition', entry)
                
                # Detect rich condition
                if entry.afr < 10.5:
                    self._record_event(cursor, 'rich_condition', entry)
            
            self.connection.commit()
            
        except Exception as e:
            logger.error(f"Event detection failed: {e}")
    
    def _record_event(self, cursor, event_type: str, entry: LogEntry):
        """Record performance event in database"""
        event_data = {
            'boost_psi': entry.boost_psi,
            'knock_retard': entry.knock_retard,
            'afr': entry.afr,
            'ignition_timing': entry.ignition_timing
        }
        
        cursor.execute('''
            INSERT INTO performance_events 
            (timestamp, event_type, event_data, rpm, speed, boost)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            event_type,
            json.dumps(event_data),
            entry.engine_rpm,
            entry.vehicle_speed,
            entry.boost_psi
        ))
    
    def _save_session_summary(self):
        """Save session summary to database"""
        try:
            if not self.session_stats['start_time']:
                return
            
            session_duration = (datetime.now() - self.session_stats['start_time']).total_seconds()
            
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO logging_sessions 
                (start_time, end_time, total_entries, max_rpm, max_boost, max_speed, max_horsepower, session_duration)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.session_stats['start_time'].isoformat(),
                datetime.now().isoformat(),
                self.session_stats['total_entries'],
                self.session_stats['max_rpm'],
                self.session_stats['max_boost'],
                self.session_stats['max_speed'],
                self.session_stats['max_horsepower'],
                session_duration
            ))
            
            self.connection.commit()
            logger.info("Session summary saved")
            
        except Exception as e:
            logger.error(f"Session summary save failed: {e}")
    
    def get_recent_data(self, seconds: float = 60.0) -> pd.DataFrame:
        """Get recent data as pandas DataFrame"""
        try:
            cutoff_time = time.time() - seconds
            
            query = '''
                SELECT * FROM tuning_logs 
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT 10000
            '''
            
            df = pd.read_sql_query(query, self.connection, params=[cutoff_time])
            return df
            
        except Exception as e:
            logger.error(f"Recent data retrieval failed: {e}")
            return pd.DataFrame()
    
    def get_session_statistics(self, session_id: int = None) -> Dict:
        """Get statistics for specific session or current session"""
        try:
            cursor = self.connection.cursor()
            
            if session_id:
                cursor.execute('''
                    SELECT * FROM logging_sessions 
                    WHERE session_id = ?
                ''', (session_id,))
            else:
                cursor.execute('''
                    SELECT * FROM logging_sessions 
                    ORDER BY session_id DESC 
                    LIMIT 1
                ''')
            
            result = cursor.fetchone()
            if result:
                return {
                    'session_id': result[0],
                    'start_time': result[1],
                    'end_time': result[2],
                    'total_entries': result[3],
                    'max_rpm': result[4],
                    'max_boost': result[5],
                    'max_speed': result[6],
                    'max_horsepower': result[7],
                    'session_duration': result[8]
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Session statistics retrieval failed: {e}")
            return {}
    
    def analyze_performance_trends(self, hours: float = 24.0) -> Dict:
        """Analyze performance trends over specified period"""
        try:
            cutoff_time = time.time() - (hours * 3600)
            
            # Get data for analysis
            query = '''
                SELECT 
                    engine_rpm, boost_psi, ignition_timing, afr, knock_retard,
                    calculated_horsepower, performance_mode
                FROM tuning_logs 
                WHERE timestamp >= ?
            '''
            
            df = pd.read_sql_query(query, self.connection, params=[cutoff_time])
            
            if df.empty:
                return {}
            
            # Calculate trends
            trends = {
                'average_horsepower': df['calculated_horsepower'].mean(),
                'max_horsepower': df['calculated_horsepower'].max(),
                'average_boost': df['boost_psi'].mean(),
                'max_boost': df['boost_psi'].max(),
                'knock_events': len(df[df['knock_retard'] < -3.0]),
                'performance_mode_usage': df['performance_mode'].value_counts().to_dict(),
                'horsepower_trend': self._calculate_trend(df, 'calculated_horsepower'),
                'boost_trend': self._calculate_trend(df, 'boost_psi')
            }
            
            return trends
            
        except Exception as e:
            logger.error(f"Performance trend analysis failed: {e}")
            return {}
    
    def _calculate_trend(self, df: pd.DataFrame, column: str) -> float:
        """Calculate linear trend for specified column"""
        if len(df) < 2:
            return 0.0
        
        try:
            x = np.arange(len(df))
            y = df[column].values
            
            # Remove NaN values
            mask = ~np.isnan(y)
            x = x[mask]
            y = y[mask]
            
            if len(x) < 2:
                return 0.0
            
            # Calculate linear regression
            slope, _ = np.polyfit(x, y, 1)
            return float(slope)
            
        except Exception:
            return 0.0
    
    def export_data(self, start_time: datetime, end_time: datetime, 
                   format: str = 'csv') -> str:
        """Export data to specified format"""
        try:
            cursor = self.connection.cursor()
            
            query = '''
                SELECT * FROM tuning_logs 
                WHERE timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp
            '''
            
            df = pd.read_sql_query(query, self.connection, 
                                 params=[start_time.timestamp(), end_time.timestamp()])
            
            if format == 'csv':
                return df.to_csv(index=False)
            elif format == 'json':
                return df.to_json(orient='records', indent=2)
            elif format == 'excel':
                # Would return file path in real implementation
                return "Excel export not implemented in this version"
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            logger.error(f"Data export failed: {e}")
            raise
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up data older than specified days"""
        try:
            cutoff_timestamp = time.time() - (days_to_keep * 24 * 3600)
            
            cursor = self.connection.cursor()
            
            # Delete old log entries
            cursor.execute('DELETE FROM tuning_logs WHERE timestamp < ?', (cutoff_timestamp,))
            
            # Delete old performance events
            cursor.execute('''
                DELETE FROM performance_events 
                WHERE datetime(timestamp) < datetime('now', ?)
            ''', (f'-{days_to_keep} days',))
            
            # Delete old sessions
            cursor.execute('''
                DELETE FROM logging_sessions 
                WHERE datetime(start_time) < datetime('now', ?)
            ''', (f'-{days_to_keep} days',))
            
            self.connection.commit()
            
            logger.info(f"Cleaned up data older than {days_to_keep} days")
            
        except Exception as e:
            logger.error(f"Data cleanup failed: {e}")

# Real-time data analysis utilities
class DataAnalyzer:
    """Real-time data analysis and pattern detection"""
    
    def __init__(self, data_logger: DataLogger):
        self.data_logger = data_logger
        
    def detect_knock_patterns(self, window_seconds: float = 10.0) -> List[Dict]:
        """Detect knock patterns in recent data"""
        try:
            df = self.data_logger.get_recent_data(window_seconds)
            
            if df.empty:
                return []
            
            # Find knock events
            knock_events = df[df['knock_retard'] < -2.0]
            
            patterns = []
            for _, event in knock_events.iterrows():
                pattern = {
                    'timestamp': event['timestamp'],
                    'rpm': event['engine_rpm'],
                    'boost': event['boost_psi'],
                    'timing': event['ignition_timing'],
                    'knock_retard': event['knock_retard'],
                    'intake_temp': event['intake_temp'],
                    'severity': 'moderate' if event['knock_retard'] > -5.0 else 'severe'
                }
                patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Knock pattern detection failed: {e}")
            return []
    
    def analyze_boost_consistency(self, window_seconds: float = 30.0) -> Dict:
        """Analyze boost pressure consistency"""
        try:
            df = self.data_logger.get_recent_data(window_seconds)
            
            if df.empty:
                return {}
            
            boost_data = df['boost_psi']
            
            analysis = {
                'average_boost': float(boost_data.mean()),
                'boost_std_dev': float(boost_data.std()),
                'boost_variance': float(boost_data.var()),
                'min_boost': float(boost_data.min()),
                'max_boost': float(boost_data.max()),
                'consistency_score': max(0, 100 - (boost_data.std() * 10))  # 0-100 score
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Boost consistency analysis failed: {e}")
            return {}
    
    def calculate_power_band(self, window_hours: float = 1.0) -> Dict:
        """Calculate engine power band characteristics"""
        try:
            df = self.data_logger.get_recent_data(window_hours * 3600)
            
            if df.empty:
                return {}
            
            # Group by RPM and calculate average power
            rpm_bins = pd.cut(df['engine_rpm'], bins=10)
            power_by_rpm = df.groupby(rpm_bins)['calculated_horsepower'].mean()
            
            power_band = {
                'peak_horsepower_rpm': float(df.loc[df['calculated_horsepower'].idxmax(), 'engine_rpm']),
                'peak_horsepower': float(df['calculated_horsepower'].max()),
                'power_band_width': float(power_by_rpm.index.right.max() - power_by_rpm.index.left.min()),
                'average_power_by_rpm': power_by_rpm.to_dict()
            }
            
            return power_band
            
        except Exception as e:
            logger.error(f"Power band calculation failed: {e}")
            return {}