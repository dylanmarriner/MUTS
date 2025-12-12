/**
 * Physics Engine
 * Main orchestrator for physics calculations and modeling
 */

import { EventEmitter } from 'events';
import { ThermodynamicsCalculator } from './thermodynamics-calculator';
import { PerformanceModeler } from './performance-modeler';
import { TurboDynamics } from './turbo-dynamics';
import { EngineSpecs, PhysicsConfig, PerformanceMetrics } from './types';

export class PhysicsEngine extends EventEmitter {
  private thermoCalc: ThermodynamicsCalculator;
  private perfModeler: PerformanceModeler;
  private turboDynamics: TurboDynamics;
  private config: PhysicsConfig;

  constructor(config?: Partial<PhysicsConfig>) {
    super();
    
    this.config = {
      airDensity: 1.225, // kg/m³ at sea level
      specificHeatRatio: 1.4, // for air
      gasConstant: 287.05, // J/(kg·K) for air
      atmosphericPressure: 101325, // Pa
      ...config
    };

    this.thermoCalc = new ThermodynamicsCalculator(this.config);
    this.perfModeler = new PerformanceModeler(this.config);
    this.turboDynamics = new TurboDynamics(this.config);
  }

  async initialize(): Promise<void> {
    await this.thermoCalc.initialize();
    await this.perfModeler.initialize();
    await this.turboDynamics.initialize();
    
    this.emit('initialized');
  }

  calculateEnginePerformance(
    rpm: number,
    boost: number,
    afr: number,
    timing: number,
    specs: EngineSpecs
  ): PerformanceMetrics {
    // Calculate volumetric efficiency
    const ve = this.thermoCalc.calculateVolumetricEfficiency(rpm, boost, specs);
    
    // Calculate air mass flow
    const airFlow = this.thermoCalc.calculateAirFlow(rpm, ve, boost, specs);
    
    // Calculate fuel flow based on AFR
    const fuelFlow = airFlow / afr;
    
    // Calculate indicated power
    const indicatedPower = this.perfModeler.calculateIndicatedPower(
      airFlow,
      fuelFlow,
      timing,
      this.config
    );
    
    // Account for friction losses
    const frictionPower = this.perfModeler.calculateFrictionLosses(rpm, specs);
    const brakePower = indicatedPower - frictionPower;
    
    // Calculate torque
    const torque = this.perfModeler.calculateTorque(brakePower, rpm);
    
    // Calculate efficiencies
    const bsfc = this.perfModeler.calculateBSFC(fuelFlow, brakePower);
    const thermalEff = this.perfModeler.calculateThermalEfficiency(
      brakePower,
      fuelFlow
    );
    
    return {
      horsepower: brakePower,
      torque,
      brakeSpecificFuelConsumption: bsfc,
      volumetricEfficiency: ve,
      thermalEfficiency: thermalEff
    };
  }

  calculateTurboOperation(
    engineRpm: number,
    exhaustFlow: number,
    targetBoost: number
  ): {
    compressorSpeed: number;
    efficiency: number;
    surgeMargin: number;
    chokeFlow: number;
  } {
    return this.turboDynamics.calculateOperatingPoint(
      engineRpm,
      exhaustFlow,
      targetBoost
    );
  }

  updateConfig(config: Partial<PhysicsConfig>): void {
    this.config = { ...this.config, ...config };
    this.thermoCalc.updateConfig(this.config);
    this.perfModeler.updateConfig(this.config);
    this.turboDynamics.updateConfig(this.config);
    
    this.emit('configUpdated', this.config);
  }

  async shutdown(): Promise<void> {
    await this.thermoCalc.shutdown();
    await this.perfModeler.shutdown();
    await this.turboDynamics.shutdown();
    
    this.emit('shutdown');
  }
}
