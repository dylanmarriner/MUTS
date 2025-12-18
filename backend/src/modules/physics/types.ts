/**
 * Physics Module Types
 * Types for engine physics calculations and modeling
 */

export interface EngineSpecs {
  displacement: number; // liters
  compressionRatio: number;
  bore: number; // mm
  stroke: number; // mm
  rodLength: number; // mm
  maxRpm: number;
  redline: number;
}

export interface ThermodynamicState {
  temperature: number; // Kelvin
  pressure: number; // Pa
  volume: number; // m³
  mass: number; // kg
}

export interface TurboSpecs {
  compressorWheelDiameter: number; // mm
  turbineWheelDiameter: number; // mm
  arRatio: number;
  maxBoost: number; // PSI
  efficiency: number; // percentage
}

export interface PerformanceMetrics {
  horsepower: number;
  torque: number;
  brakeSpecificFuelConsumption: number;
  volumetricEfficiency: number;
  thermalEfficiency: number;
}

export interface PhysicsConfig {
  airDensity: number; // kg/m³
  specificHeatRatio: number;
  gasConstant: number; // J/(kg·K)
  atmosphericPressure: number; // Pa
}
