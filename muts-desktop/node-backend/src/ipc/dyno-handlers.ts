/**
 * Dyno IPC Handlers
 * Handles all dyno-related IPC communication with constants enforcement
 */

import { ipcMain } from 'electron';
import { Logger } from '../utils/logger';
import { VehicleConstantsManager } from '../../core/tuning/vehicle_constants';
import { DynoMathEnhanced } from '../../core/tuning/dyno_math_enhanced';
import { get_dyno_persistence } from '../../core/tuning/dyno_persistence';

interface BackendContext {
  databaseManager: any;
  sessionManager: any;
}

const logger = new Logger('DynoIPCHandlers');

// Global instances
let constantsManager: VehicleConstantsManager;
let dynoPersistence = get_dyno_persistence();

export function registerDynoHandlers(context: BackendContext): void {
  // Initialize constants manager
  constantsManager = new VehicleConstantsManager();

  // Get vehicle constants
  ipcMain.handle('dyno:getConstants', async () => {
    try {
      // Try to load active constants for default vehicle
      const constants = constantsManager.load_constants('sim_mazdaspeed3');
      
      return {
        success: true,
        constants: {
          vehicle_mass: constants.vehicle_mass,
          driver_fuel_mass: constants.driver_fuel_mass,
          drag_coefficient: constants.drag_coefficient,
          frontal_area: constants.frontal_area,
          gear_ratios: constants.gear_ratios,
          final_drive_ratio: constants.final_drive_ratio,
          drivetrain_efficiency: constants.drivetrain_efficiency,
          tire_radius: constants.tire_radius,
          version: constants.version,
          source: constants.source
        }
      };
    } catch (error) {
      logger.error('Failed to load constants:', error);
      return {
        success: false,
        error: error.message || 'No vehicle constants found'
      };
    }
  });

  // Save vehicle constants
  ipcMain.handle('dyno:saveConstants', async (event, constantsData) => {
    try {
      // Import VehicleConstants
      const { VehicleConstants } = require('../../core/tuning/vehicle_constants');
      
      // Create constants object
      const constants = new VehicleConstants({
        ...constantsData,
        created_at: new Date()
      });
      
      // Save to database
      const id = constantsManager.save_constants('sim_mazdaspeed3', constants);
      
      return {
        success: true,
        id: id,
        version: constants.version
      };
    } catch (error) {
      logger.error('Failed to save constants:', error);
      return {
        success: false,
        error: error.message || 'Failed to save constants'
      };
    }
  });

  // Start dyno run
  ipcMain.handle('dyno:startRun', async (event, options) => {
    try {
      // Load constants
      const constants = constantsManager.load_constants('sim_mazdaspeed3');
      
      // Initialize dyno math with constants
      const dynoMath = new DynoMathEnhanced(constants);
      
      // Generate simulated acceleration data
      const { speedData, timeData } = await generateSimulatedRun();
      
      // Calculate power
      const run = dynoMath.calculate_power_from_acceleration(
        speedData,
        timeData,
        null, // Default config
        options.telemetrySource || 'simulation',
        options.useSimulation || true
      );
      
      // Save run to database
      const runId = dynoPersistence.save_run(run);
      
      // Convert to serializable format
      const result = {
        run_id: runId,
        constants_version: run.constants_version,
        telemetry_source: run.telemetry_source,
        timestamp: run.timestamp.toISOString(),
        simulation: run.simulation,
        max_power: run.max_power,
        max_torque: run.max_torque,
        measurement_count: run.measurements.length,
        measurements: run.measurements.map(m => ({
          rpm: m.rpm,
          torque: m.torque,
          power: m.power,
          wheel_power: m.wheel_power,
          wheel_torque: m.wheel_torque,
          gear: m.gear
        })),
        calculation_trace: run.calculation_trace
      };
      
      return {
        success: true,
        run: result
      };
    } catch (error) {
      logger.error('Failed to start dyno run:', error);
      return {
        success: false,
        error: error.message || 'Dyno run failed'
      };
    }
  });

  // Get dyno run history
  ipcMain.handle('dyno:getHistory', async (event, options) => {
    try {
      const runs = dynoPersistence.list_runs(
        options.limit || 10,
        options.simulationOnly
      );
      
      return {
        success: true,
        runs: runs
      };
    } catch (error) {
      logger.error('Failed to get dyno history:', error);
      return {
        success: false,
        error: error.message || 'Failed to get history'
      };
    }
  });

  // Load specific dyno run
  ipcMain.handle('dyno:loadRun', async (event, runId) => {
    try {
      const run = dynoPersistence.load_run(runId);
      
      if (!run) {
        return {
          success: false,
          error: 'Run not found'
        };
      }
      
      const result = {
        run_id: runId,
        constants_version: run.constants_version,
        telemetry_source: run.telemetry_source,
        timestamp: run.timestamp.toISOString(),
        simulation: run.simulation,
        max_power: run.max_power,
        max_torque: run.max_torque,
        measurement_count: run.measurements.length,
        measurements: run.measurements.map(m => ({
          rpm: m.rpm,
          torque: m.torque,
          power: m.power,
          wheel_power: m.wheel_power,
          wheel_torque: m.wheel_torque,
          gear: m.gear
        })),
        calculation_trace: run.calculation_trace
      };
      
      return {
        success: true,
        run: result
      };
    } catch (error) {
      logger.error('Failed to load dyno run:', error);
      return {
        success: false,
        error: error.message || 'Failed to load run'
      };
    }
  });

  // Export dyno run
  ipcMain.handle('dyno:exportRun', async (event, runId, format) => {
    try {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const filename = `dyno_run_${runId}_${timestamp}.${format}`;
      
      if (format === 'json') {
        const run = dynoPersistence.load_run(runId);
        if (!run) {
          throw new Error('Run not found');
        }
        
        const exportData = {
          run_id: runId,
          constants_version: run.constants_version,
          telemetry_source: run.telemetry_source,
          timestamp: run.timestamp.toISOString(),
          simulation: run.simulation,
          max_power: run.max_power,
          max_torque: run.max_torque,
          measurements: run.measurements,
          calculation_trace: run.calculation_trace
        };
        
        return {
          success: true,
          filename: filename,
          data: JSON.stringify(exportData, null, 2)
        };
      }
      
      throw new Error(`Unsupported export format: ${format}`);
    } catch (error) {
      logger.error('Failed to export dyno run:', error);
      return {
        success: false,
        error: error.message || 'Export failed'
      };
    }
  });

  logger.info('Dyno IPC handlers registered');
}

/**
 * Generate simulated acceleration data for dyno run
 */
async function generateSimulatedRun() {
  // Simulate a 3rd gear pull from 2000 to 6500 RPM
  const sampleRate = 20; // Hz
  const duration = 10; // seconds
  const samples = duration * sampleRate;
  
  const speedData: number[] = [];
  const timeData: number[] = [];
  
  // Mazdaspeed 3 constants
  const gearRatio = 1.171; // 3rd gear
  const finalDrive = 3.529;
  const tireRadius = 0.318; // m
  
  for (let i = 0; i < samples; i++) {
    const t = i / sampleRate;
    timeData.push(t);
    
    // Simulate RPM curve
    let rpm;
    if (t < 2) {
      rpm = 2000 + (t / 2) * 1000; // 2000 to 3000
    } else if (t < 6) {
      rpm = 3000 + ((t - 2) / 4) * 2500; // 3000 to 5500
    } else {
      rpm = 5500 + ((t - 6) / 4) * 1000; // 5500 to 6500
    }
    
    // Convert RPM to speed
    const wheelRpm = rpm / (gearRatio * finalDrive);
    const speed = wheelRpm * 2 * Math.PI * tireRadius / 60; // m/s
    
    speedData.push(speed);
  }
  
  return { speedData, timeData };
}
