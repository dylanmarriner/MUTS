/**
 * Performance Modeler
 * Models engine performance metrics and characteristics
 */

import { EventEmitter } from 'events';
import { EngineSpecs, PhysicsConfig } from './types';

export class PerformanceModeler extends EventEmitter {
  private config: PhysicsConfig;

  constructor(config: PhysicsConfig) {
    super();
    this.config = config;
  }

  async initialize(): Promise<void> {
    this.emit('initialized');
  }

  calculateIndicatedPower(
    airFlow: number, // kg/s
    fuelFlow: number, // kg/s
    timing: number, // degrees BTDC
    config: PhysicsConfig
  ): number {
    // Calculate energy release from fuel
    const fuelEnergyDensity = 43000000; // J/kg for gasoline
    const combustionEnergy = fuelFlow * fuelEnergyDensity;
    
    // Timing efficiency factor
    const optimalTiming = 25; // degrees BTDC
    const timingError = Math.abs(timing - optimalTiming);
    const timingEfficiency = Math.max(0.7, 1 - (timingError * 0.01));
    
    // Indicated power with timing correction
    const indicatedPower = combustionEnergy * timingEfficiency * 0.35; // 35% thermal efficiency
    
    return indicatedPower;
  }

  calculateFrictionLosses(rpm: number, specs: EngineSpecs): number {
    // FMEP (Friction Mean Effective Pressure) model
    const baseFMEP = 100; // kPa at 1000 RPM
    const rpmFactor = Math.pow(rpm / 1000, 1.5);
    const displacementM3 = specs.displacement / 1000;
    
    const fMEP = baseFMEP * rpmFactor; // kPa
    const frictionPower = (fMEP * 1000 * displacementM3 * rpm) / (60 * 2); // Watts
    
    return frictionPower;
  }

  calculateTorque(power: number, rpm: number): number {
    // Torque = Power / Angular velocity
    const angularVelocity = (rpm * 2 * Math.PI) / 60; // rad/s
    return power / angularVelocity; // Nm
  }

  calculateBSFC(fuelFlow: number, brakePower: number): number {
    // Brake Specific Fuel Consumption in g/kWh
    if (brakePower <= 0) return 0;
    
    const fuelFlowGramsPerHour = fuelFlow * 3600 * 1000; // g/hr
    const brakePowerKilowatts = brakePower / 1000; // kW
    
    return fuelFlowGramsPerHour / brakePowerKilowatts; // g/kWh
  }

  calculateThermalEfficiency(brakePower: number, fuelFlow: number): number {
    // Thermal efficiency as percentage
    const fuelEnergyDensity = 43000000; // J/kg
    const fuelPower = fuelFlow * fuelEnergyDensity; // J/s (Watts)
    
    if (fuelPower <= 0) return 0;
    
    return (brakePower / fuelPower) * 100; // percentage
  }

  calculateVolumetricEfficiency(
    rpm: number,
    manifoldPressure: number,
    specs: EngineSpecs
  ): number {
    // Simplified VE model
    const peakTorqueRpm = specs.maxRpm * 0.55;
    const rpmRatio = rpm / peakTorqueRpm;
    
    let ve = 0.85; // Base VE
    
    if (rpmRatio <= 1) {
      ve = 0.85 + 0.1 * rpmRatio; // Rise to 95%
    } else {
      ve = 0.95 * Math.exp(-0.3 * Math.pow(rpmRatio - 1, 2)); // Fall off after peak
    }
    
    // Pressure effect
    const pressureRatio = manifoldPressure / this.config.atmosphericPressure;
    ve *= Math.min(1.1, 1 + 0.05 * Math.log(pressureRatio));
    
    return Math.min(1.0, ve);
  }

  updateConfig(config: PhysicsConfig): void {
    this.config = config;
    this.emit('configUpdated', config);
  }

  async shutdown(): Promise<void> {
    this.emit('shutdown');
  }
}
