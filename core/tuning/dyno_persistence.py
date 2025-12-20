#!/usr/bin/env python3
"""
Dyno Run Persistence
Stores dyno run results with full audit trail
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import sqlite3

from core.tuning.dyno_math_enhanced import DynoRun, PowerMeasurement

logger = logging.getLogger(__name__)

@dataclass
class DynoRunRecord:
    """Database record for a dyno run"""
    id: Optional[int]
    run_id: str
    constants_version: int
    telemetry_source: str
    timestamp: datetime
    simulation: bool
    max_power: float
    max_torque: float
    measurement_count: int
    run_data_json: str
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        if self.timestamp:
            data['timestamp'] = self.timestamp.isoformat()
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        return data

class DynoRunPersistence:
    """Manages dyno run persistence with database storage"""
    
    def __init__(self, db_path: str = "dyno_runs.db"):
        self.db_path = db_path
        self._init_database()
        logger.info(f"DynoRunPersistence initialized with DB: {db_path}")
    
    def _init_database(self) -> None:
        """Initialize the database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS dyno_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT UNIQUE NOT NULL,
                    constants_version INTEGER NOT NULL,
                    telemetry_source TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    simulation BOOLEAN NOT NULL,
                    max_power REAL NOT NULL,
                    max_torque REAL NOT NULL,
                    measurement_count INTEGER NOT NULL,
                    run_data_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_runs_timestamp 
                ON dyno_runs(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_runs_simulation 
                ON dyno_runs(simulation)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_runs_constants 
                ON dyno_runs(constants_version)
            """)
            
            conn.commit()
    
    def save_run(self, run: DynoRun, run_id: Optional[str] = None) -> str:
        """Save a dyno run to database"""
        if not run_id:
            run_id = f"dyno_{int(run.timestamp.timestamp())}_{hash(str(run.run_data_json)) % 10000:04d}"
        
        # Convert measurements to serializable format
        measurements_data = []
        for m in run.measurements:
            measurements_data.append({
                'rpm': m.rpm,
                'torque': m.torque,
                'power': m.power,
                'wheel_power': m.wheel_power,
                'wheel_torque': m.wheel_torque,
                'timestamp': m.timestamp,
                'gear': m.gear
            })
        
        # Prepare run data
        run_data = {
            'measurements': measurements_data,
            'power_curve': run.power_curve.tolist() if run.power_curve.size > 0 else [],
            'torque_curve': run.torque_curve.tolist() if run.torque_curve.size > 0 else [],
            'unit': run.unit.value,
            'calculation_trace': run.calculation_trace
        }
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO dyno_runs 
                (run_id, constants_version, telemetry_source, timestamp, 
                 simulation, max_power, max_torque, measurement_count, 
                 run_data_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id,
                run.constants_version,
                run.telemetry_source,
                run.timestamp.isoformat(),
                run.simulation,
                run.max_power,
                run.max_torque,
                len(run.measurements),
                json.dumps(run_data),
                datetime.utcnow().isoformat()
            ))
            
            conn.commit()
        
        logger.info(f"Saved dyno run {run_id} with {len(run.measurements)} measurements")
        return run_id
    
    def load_run(self, run_id: str) -> Optional[DynoRun]:
        """Load a dyno run from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT run_data_json, constants_version, telemetry_source, 
                       timestamp, simulation, max_power, max_torque
                FROM dyno_runs WHERE run_id = ?
            """, (run_id,))
            
            row = cursor.fetchone()
            if not row:
                logger.warning(f"Dyno run {run_id} not found")
                return None
            
            # Reconstruct run data
            run_data = json.loads(row[0])
            measurements = []
            
            for m_data in run_data['measurements']:
                measurements.append(PowerMeasurement(
                    rpm=m_data['rpm'],
                    torque=m_data['torque'],
                    power=m_data['power'],
                    wheel_power=m_data['wheel_power'],
                    wheel_torque=m_data['wheel_torque'],
                    timestamp=m_data.get('timestamp'),
                    gear=m_data.get('gear')
                ))
            
            # Convert curves back to numpy arrays
            power_curve = run_data.get('power_curve', [])
            torque_curve = run_data.get('torque_curve', [])
            
            return DynoRun(
                measurements=measurements,
                max_power=row[5],
                max_torque=row[6],
                power_curve=power_curve,
                torque_curve=torque_curve,
                unit=run_data['unit'],
                constants_version=row[1],
                telemetry_source=row[2],
                timestamp=datetime.fromisoformat(row[3]),
                simulation=row[4],
                calculation_trace=run_data.get('calculation_trace', [])
            )
    
    def list_runs(self, limit: int = 50, simulation_only: Optional[bool] = None) -> List[Dict[str, Any]]:
        """List dyno runs"""
        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT run_id, constants_version, telemetry_source, timestamp,
                       simulation, max_power, max_torque, measurement_count, created_at
                FROM dyno_runs
            """
            params = []
            
            if simulation_only is not None:
                query += " WHERE simulation = ?"
                params.append(simulation_only)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor = conn.execute(query, params)
            
            runs = []
            for row in cursor.fetchall():
                runs.append({
                    'run_id': row[0],
                    'constants_version': row[1],
                    'telemetry_source': row[2],
                    'timestamp': row[3],
                    'simulation': bool(row[4]),
                    'max_power': row[5],
                    'max_torque': row[6],
                    'measurement_count': row[7],
                    'created_at': row[8]
                })
            
            return runs
    
    def delete_run(self, run_id: str) -> bool:
        """Delete a dyno run"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM dyno_runs WHERE run_id = ?",
                (run_id,)
            )
            conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"Deleted dyno run {run_id}")
                return True
            else:
                logger.warning(f"Dyno run {run_id} not found for deletion")
                return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get dyno run statistics"""
        with sqlite3.connect(self.db_path) as conn:
            # Total runs
            total_runs = conn.execute("SELECT COUNT(*) FROM dyno_runs").fetchone()[0]
            
            # Simulation runs
            sim_runs = conn.execute("SELECT COUNT(*) FROM dyno_runs WHERE simulation = 1").fetchone()[0]
            
            # Real runs
            real_runs = total_runs - sim_runs
            
            # Best power
            best_power = conn.execute("SELECT MAX(max_power) FROM dyno_runs").fetchone()[0] or 0
            
            # Best torque
            best_torque = conn.execute("SELECT MAX(max_torque) FROM dyno_runs").fetchone()[0] or 0
            
            # Constants versions used
            versions = conn.execute("""
                SELECT DISTINCT constants_version, COUNT(*) 
                FROM dyno_runs 
                GROUP BY constants_version 
                ORDER BY constants_version
            """).fetchall()
            
            return {
                'total_runs': total_runs,
                'simulation_runs': sim_runs,
                'real_runs': real_runs,
                'best_power_kw': best_power,
                'best_torque_nm': best_torque,
                'constants_versions': dict(versions)
            }
    
    def export_runs(self, filepath: str, run_ids: Optional[List[str]] = None) -> None:
        """Export runs to JSON file"""
        runs_data = []
        
        if run_ids:
            # Export specific runs
            for run_id in run_ids:
                run = self.load_run(run_id)
                if run:
                    runs_data.append({
                        'run_id': run_id,
                        'constants_version': run.constants_version,
                        'telemetry_source': run.telemetry_source,
                        'timestamp': run.timestamp.isoformat(),
                        'simulation': run.simulation,
                        'max_power': run.max_power,
                        'max_torque': run.max_torque,
                        'measurements': [
                            {
                                'rpm': m.rpm,
                                'torque': m.torque,
                                'power': m.power,
                                'wheel_power': m.wheel_power,
                                'wheel_torque': m.wheel_torque,
                                'gear': m.gear
                            } for m in run.measurements
                        ],
                        'calculation_trace': run.calculation_trace
                    })
        else:
            # Export all runs summary
            runs = self.list_runs(limit=1000)
            runs_data = runs
        
        with open(filepath, 'w') as f:
            json.dump({
                'exported_at': datetime.utcnow().isoformat(),
                'run_count': len(runs_data),
                'runs': runs_data
            }, f, indent=2)
        
        logger.info(f"Exported {len(runs_data)} runs to {filepath}")

# Global instance
_dyno_persistence: Optional[DynoRunPersistence] = None

def get_dyno_persistence() -> DynoRunPersistence:
    """Get the global dyno persistence instance"""
    global _dyno_persistence
    if _dyno_persistence is None:
        _dyno_persistence = DynoRunPersistence()
    return _dyno_persistence
