/**
 * Thermodynamics Calculator
 * Calculates engine thermodynamic properties and processes
 */

import { EventEmitter } from 'events';
import { EngineSpecs, PhysicsConfig, ThermodynamicState } from './types';

export class ThermodynamicsCalculator extends EventEmitter {
  private config: PhysicsConfig;

  constructor(config: PhysicsConfig) {
    super();
    this.config = config;
  }

  async initialize(): Promise<void> {
    this.emit('initialized');
  }

  calculateVolumetricEfficiency(
    rpm: number,
    boost: number, // PSI
    specs: EngineSpecs
  ): number {
    // Base VE curve
    let baseVE = 0.85; // 85% at low RPM
    
    // Peak torque RPM optimization
    const peakTorqueRpm = specs.maxRpm * 0.55;
    const rpmRatio = rpm / peakTorqueRpm;
    
    if (rpmRatio <= 1) {
      baseVE = 0.85 + (0.95 - 0.85) * rpmRatio; // Rise to 95% at peak torque
    } else {
      // Decline after peak torque
      baseVE = 0.95 * Math.exp(-0.5 * Math.pow(rpmRatio - 1, 2));
    }
    
    // Boost effect on VE
    const boostKpa = boost * 6.895; // Convert PSI to kPa
    const pressureRatio = (this.config.atmosphericPressure + boostKpa * 1000) / this.config.atmosphericPressure;
    const boostEffect = Math.min(1.1, 1 + 0.05 * Math.log(pressureRatio));
    
    return Math.min(1.0, baseVE * boostEffect);
  }

  calculateAirFlow(
    rpm: number,
    volumetricEfficiency: number,
    boost: number, // PSI
    specs: EngineSpecs
  ): number {
    // Calculate theoretical air flow
    const displacementM3 = specs.displacement / 1000; // Convert liters to m³
    const revolutionsPerSecond = rpm / 60;
    const intakeEventsPerSecond = revolutionsPerSecond * specs.compressionRatio / 2;
    
    const theoreticalFlow = displacementM3 * intakeEventsPerSecond * this.config.airDensity;
    
    // Apply VE and boost correction
    const boostKpa = boost * 6.895;
    const pressureRatio = (this.config.atmosphericPressure + boostKpa * 1000) / this.config.atmosphericPressure;
    const densityCorrection = pressureRatio * (this.config.atmosphericPressure / (this.config.atmosphericPressure + boostKpa * 1000));
    
    return theoreticalFlow * volumetricEfficiency * densityCorrection;
  }

  calculateIntakeChargeTemperature(
    ambientTemp: number, // Celsius
    boostPressure: number, // PSI
    compressorEfficiency: number
  ): number {
    const ambientKelvin = ambientTemp + 273.15;
    const pressureRatio = (this.config.atmosphericPressure + boostPressure * 6895) / this.config.atmosphericPressure;
    
    // Ideal compression temperature
    const idealTemp = ambientKelvin * Math.pow(pressureRatio, (this.config.specificHeatRatio - 1) / this.config.specificHeatRatio);
    
    // Account for compressor efficiency
    const actualTemp = ambientKelvin + (idealTemp - ambientKelvin) / (compressorEfficiency / 100);
    
    return actualTemp - 273.15; // Convert back to Celsius
  }

  calculateExhaustGasTemperature(
    intakeTemp: number, // Celsius
    afr: number,
    loadFactor: number // 0-1
  ): number {
    const intakeKelvin = intakeTemp + 273.15;
    
    // Base EGT calculation
    const combustionTempRise = 800 * (14.7 / afr); // Temperature rise from combustion
    const loadEffect = 600 * loadFactor; // Load-dependent temperature
    
    const egtKelvin = intakeKelvin + combustionTempRise + loadEffect;
    
    return egtKelvin - 273.15; // Convert to Celsius
  }

  updateConfig(config: PhysicsConfig): void {
    this.config = config;
    this.emit('configUpdated', config);
  }

  async shutdown(): Promise<void> {
    this.emit('shutdown');
  }
}
