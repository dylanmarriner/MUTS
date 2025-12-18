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
                CREATE TABLE IF NOT EXISTS session_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_start TEXT NOT NULL,
                    session_end TEXT,
                    total_entries INTEGER,
                    max_rpm REAL,
                    max_boost REAL,
                    max_speed REAL,
                    max_horsepower REAL,
                    avg_afr REAL,
                    total_distance REAL,
                    notes TEXT
                )
            ''')
            
            # Create performance events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    event_type TEXT NOT NULL,
                    event_value REAL,
                    description TEXT,
                    session_id INTEGER
                )
            ''')
            
            self.connection.commit()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
    
    def start_logging(self, session_name: str = None):
        """Start data logging session"""
        if self.logging_active:
            logger.warning("Logging already active")
            return
        
        self.logging_active = True
        self.shutdown_flag.clear()
        
        # Initialize session
        self.session_stats['start_time'] = datetime.now()
        self.session_stats['total_entries'] = 0
        self.session_stats['max_rpm'] = 0
        self.session_stats['max_boost'] = 0
        self.session_stats['max_speed'] = 0
        self.session_stats['max_horsepower'] = 0
        
        # Start logging thread
        self.logging_thread = threading.Thread(target=self._logging_loop)
        self.logging_thread.daemon = True
        self.logging_thread.start()
        
        # Start processing thread
        self.processing_thread = threading.Thread(target=self._processing_loop)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        logger.info(f"Started logging session: {session_name or 'unnamed'}")
    
    def stop_logging(self):
        """Stop data logging session"""
        if not self.logging_active:
            return
        
        self.logging_active = False
        self.shutdown_flag.set()
        
        # Wait for threads
        if self.logging_thread:
            self.logging_thread.join(timeout=5)
        if self.processing_thread:
            self.processing_thread.join(timeout=5)
        
        # Save session summary
        self._save_session_summary()
        
        logger.info("Logging session stopped")
    
    def log_data(self, sensor_data: Dict, tuning_params: Dict = None):
        """Log sensor data"""
        if not self.logging_active:
            return
        
        # Create log entry
        entry = LogEntry(
            timestamp=time.time(),
            engine_rpm=sensor_data.get('engine_rpm', 0),
            vehicle_speed=sensor_data.get('vehicle_speed', 0),
            throttle_position=sensor_data.get('throttle_position', 0),
            boost_psi=sensor_data.get('boost_psi', 0),
            ignition_timing=sensor_data.get('ignition_timing', 0),
            afr=sensor_data.get('afr', 14.7),
            knock_retard=sensor_data.get('knock_retard', 0),
            intake_temp=sensor_data.get('intake_temp', 25),
            coolant_temp=sensor_data.get('coolant_temp', 90),
            mass_airflow=sensor_data.get('mass_airflow', 0),
            vvt_intake_angle=sensor_data.get('vvt_intake_angle', 0),
            vvt_exhaust_angle=sensor_data.get('vvt_exhaust_angle', 0),
            fuel_trim_long=sensor_data.get('fuel_trim_long', 0),
            fuel_trim_short=sensor_data.get('fuel_trim_short', 0),
            calculated_torque=sensor_data.get('calculated_torque', 0),
            calculated_horsepower=sensor_data.get('calculated_horsepower', 0),
            performance_mode=sensor_data.get('performance_mode', 'street'),
            tuning_adjustments=tuning_params or {}
        )
        
        # Add to buffer
        with self.buffer_lock:
            self.realtime_buffer.append(entry)
            
            # Limit buffer size
            if len(self.realtime_buffer) > self.max_memory_entries:
                self.realtime_buffer = self.realtime_buffer[-self.max_memory_entries:]
    
    def _logging_loop(self):
        """Main logging loop"""
        while self.logging_active and not self.shutdown_flag.is_set():
            try:
                # Process buffer
                entries_to_save = []
                
                with self.buffer_lock:
                    if self.realtime_buffer:
                        entries_to_save = self.realtime_buffer.copy()
                        self.realtime_buffer.clear()
                
                # Save to database
                if entries_to_save:
                    self._save_entries(entries_to_save)
                
                time.sleep(self.log_interval)
                
            except Exception as e:
                logger.error(f"Logging loop error: {e}")
                time.sleep(1)
    
    def _processing_loop(self):
        """Data processing loop"""
        while self.logging_active and not self.shutdown_flag.is_set():
            try:
                # Detect performance events
                self._detect_performance_events()
                
                # Update statistics
                self._update_statistics()
                
                time.sleep(1.0)  # 1 Hz processing
                
            except Exception as e:
                logger.error(f"Processing loop error: {e}")
                time.sleep(1)
    
    def _save_entries(self, entries: List[LogEntry]):
        """Save log entries to database"""
        try:
            cursor = self.connection.cursor()
            
            for entry in entries:
                cursor.execute('''
                    INSERT INTO tuning_logs (
                        timestamp, engine_rpm, vehicle_speed, throttle_position,
                        boost_psi, ignition_timing, afr, knock_retard,
                        intake_temp, coolant_temp, mass_airflow,
                        vvt_intake_angle, vvt_exhaust_angle, fuel_trim_long,
                        fuel_trim_short, calculated_torque, calculated_horsepower,
                        performance_mode, tuning_adjustments
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    entry.timestamp, entry.engine_rpm, entry.vehicle_speed,
                    entry.throttle_position, entry.boost_psi, entry.ignition_timing,
                    entry.afr, entry.knock_retard, entry.intake_temp,
                    entry.coolant_temp, entry.mass_airflow, entry.vvt_intake_angle,
                    entry.vvt_exhaust_angle, entry.fuel_trim_long,
                    entry.fuel_trim_short, entry.calculated_torque,
                    entry.calculated_horsepower, entry.performance_mode,
                    json.dumps(entry.tuning_adjustments)
                ))
                
                # Update session stats
                self.session_stats['total_entries'] += 1
                self.session_stats['max_rpm'] = max(self.session_stats['max_rpm'], entry.engine_rpm)
                self.session_stats['max_boost'] = max(self.session_stats['max_boost'], entry.boost_psi)
                self.session_stats['max_speed'] = max(self.session_stats['max_speed'], entry.vehicle_speed)
                self.session_stats['max_horsepower'] = max(self.session_stats['max_horsepower'], entry.calculated_horsepower)
            
            self.connection.commit()
            
        except Exception as e:
            logger.error(f"Failed to save entries: {e}")
    
    def _detect_performance_events(self):
        """Detect performance events in real-time data"""
        # Get recent data
        recent_data = self.get_recent_data(100)
        
        if len(recent_data) < 10:
            return
        
        # Detect boost spike
        boost_values = [d['boost_psi'] for d in recent_data]
        if max(boost_values) > 20.0:
            self._log_performance_event('boost_spike', max(boost_values), 'High boost detected')
        
        # Detect knock event
        knock_values = [d['knock_retard'] for d in recent_data]
        if min(knock_values) < -2.0:
            self._log_performance_event('knock_event', min(knock_values), 'Knock detected')
        
        # Detect high RPM
        rpm_values = [d['engine_rpm'] for d in recent_data]
        if max(rpm_values) > 6500:
            self._log_performance_event('high_rpm', max(rpm_values), 'High RPM operation')
    
    def _log_performance_event(self, event_type: str, value: float, description: str):
        """Log performance event"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO performance_events (timestamp, event_type, event_value, description)
                VALUES (?, ?, ?, ?)
            ''', (time.time(), event_type, value, description))
            self.connection.commit()
            
        except Exception as e:
            logger.error(f"Failed to log performance event: {e}")
    
    def _update_statistics(self):
        """Update session statistics"""
        # Calculate additional stats
        recent_data = self.get_recent_data(1000)
        
        if recent_data:
            # Average AFR
            afr_values = [d['afr'] for d in recent_data if d['afr'] > 0]
            if afr_values:
                self.session_stats['avg_afr'] = np.mean(afr_values)
            
            # Total distance (estimated)
            speed_values = [d['vehicle_speed'] for d in recent_data]
            if speed_values:
                # Convert km/h to km and estimate distance
                avg_speed = np.mean(speed_values)
                time_hours = len(recent_data) * self.log_interval / 3600
                distance = avg_speed * time_hours
                self.session_stats['total_distance'] = self.session_stats.get('total_distance', 0) + distance
    
    def _save_session_summary(self):
        """Save session summary to database"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO session_summaries (
                    session_start, session_end, total_entries, max_rpm,
                    max_boost, max_speed, max_horsepower, avg_afr, total_distance
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.session_stats['start_time'].isoformat(),
                datetime.now().isoformat(),
                self.session_stats['total_entries'],
                self.session_stats['max_rpm'],
                self.session_stats['max_boost'],
                self.session_stats['max_speed'],
                self.session_stats['max_horsepower'],
                self.session_stats.get('avg_afr', 0),
                self.session_stats.get('total_distance', 0)
            ))
            self.connection.commit()
            
        except Exception as e:
            logger.error(f"Failed to save session summary: {e}")
    
    def get_recent_data(self, count: int = 100) -> List[Dict]:
        """Get recent data entries"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT * FROM tuning_logs
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (count,))
            
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            data = []
            for row in rows:
                entry = dict(zip(columns, row))
                # Parse tuning adjustments
                if entry['tuning_adjustments']:
                    entry['tuning_adjustments'] = json.loads(entry['tuning_adjustments'])
                data.append(entry)
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to get recent data: {e}")
            return []
    
    def export_data(self, start_time: float = None, end_time: float = None, 
                   format: str = 'csv') -> Optional[str]:
        """Export data to file"""
        try:
            # Build query
            query = "SELECT * FROM tuning_logs WHERE 1=1"
            params = []
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)
            
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)
            
            query += " ORDER BY timestamp"
            
            # Get data
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            # Create DataFrame
            df = pd.DataFrame(rows, columns=columns)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if format.lower() == 'csv':
                filename = f"mazdaspeed3_log_{timestamp}.csv"
                df.to_csv(filename, index=False)
            elif format.lower() == 'excel':
                filename = f"mazdaspeed3_log_{timestamp}.xlsx"
                df.to_excel(filename, index=False)
            elif format.lower() == 'json':
                filename = f"mazdaspeed3_log_{timestamp}.json"
                df.to_json(filename, orient='records', indent=2)
            else:
                logger.error(f"Unsupported export format: {format}")
                return None
            
            logger.info(f"Data exported to: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Failed to export data: {e}")
            return None
    
    def analyze_performance(self, start_time: float = None, end_time: float = None) -> Dict:
        """Analyze performance data"""
        try:
            # Get data
            data = self.get_recent_data(10000)  # Get last 10k entries
            
            if not data:
                return {}
            
            # Calculate statistics
            df = pd.DataFrame(data)
            
            analysis = {
                'general_stats': {
                    'total_entries': len(df),
                    'time_range': {
                        'start': df['timestamp'].min(),
                        'end': df['timestamp'].max()
                    },
                    'duration_hours': (df['timestamp'].max() - df['timestamp'].min()) / 3600
                },
                'performance_stats': {
                    'max_rpm': df['engine_rpm'].max(),
                    'avg_rpm': df['engine_rpm'].mean(),
                    'max_boost': df['boost_psi'].max(),
                    'avg_boost': df['boost_psi'].mean(),
                    'max_hp': df['calculated_horsepower'].max(),
                    'avg_hp': df['calculated_horsepower'].mean(),
                    'max_torque': df['calculated_torque'].max(),
                    'avg_torque': df['calculated_torque'].mean()
                },
                'fuel_stats': {
                    'avg_afr': df['afr'].mean(),
                    'min_afr': df['afr'].min(),
                    'max_afr': df['afr'].max()
                },
                'temperature_stats': {
                    'avg_coolant': df['coolant_temp'].mean(),
                    'max_coolant': df['coolant_temp'].max(),
                    'avg_intake': df['intake_temp'].mean(),
                    'max_intake': df['intake_temp'].max()
                }
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze performance: {e}")
            return {}
    
    def cleanup_old_data(self, days: int = 30):
        """Clean up old data from database"""
        try:
            cutoff_time = time.time() - (days * 24 * 3600)
            
            cursor = self.connection.cursor()
            
            # Delete old logs
            cursor.execute("DELETE FROM tuning_logs WHERE timestamp < ?", (cutoff_time,))
            deleted_logs = cursor.rowcount
            
            # Delete old events
            cursor.execute("DELETE FROM performance_events WHERE timestamp < ?", (cutoff_time,))
            deleted_events = cursor.rowcount
            
            self.connection.commit()
            
            logger.info(f"Cleaned up {deleted_logs} log entries and {deleted_events} events")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
    
    def get_session_stats(self) -> Dict:
        """Get current session statistics"""
        return self.session_stats.copy()
