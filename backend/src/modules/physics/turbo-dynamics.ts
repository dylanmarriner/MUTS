/**
 * Turbo Dynamics
 * Models turbocharger behavior and performance
 */

import { EventEmitter } from 'events';
import { TurboSpecs, PhysicsConfig } from './types';

export class TurboDynamics extends EventEmitter {
  private config: PhysicsConfig;
  private compressorMap: Map<string, number[][]> = new Map();

  constructor(config: PhysicsConfig) {
    super();
    this.config = config;
  }

  async initialize(): Promise<void> {
    // Initialize compressor maps
    this.initializeCompressorMaps();
    this.emit('initialized');
  }

  calculateOperatingPoint(
    engineRpm: number,
    exhaustFlow: number, // kg/s
    targetBoost: number // PSI
  ): {
    compressorSpeed: number;
    efficiency: number;
    surgeMargin: number;
    chokeFlow: number;
  } {
    // Calculate required pressure ratio
    const targetBoostKpa = targetBoost * 6.895;
    const pressureRatio = (this.config.atmosphericPressure + targetBoostKpa * 1000) / this.config.atmosphericPressure;
    
    // Estimate compressor speed based on pressure ratio and flow
    const correctedFlow = this.correctFlow(exhaustFlow, targetBoost);
    const compressorSpeed = this.estimateSpeed(pressureRatio, correctedFlow);
    
    // Get efficiency from compressor map
    const efficiency = this.getCompressorEfficiency(pressureRatio, correctedFlow);
    
    // Calculate surge and choke margins
    const surgeLine = this.getSurgeLine(correctedFlow);
    const surgeMargin = ((pressureRatio - surgeLine) / pressureRatio) * 100;
    
    const chokeFlow = this.getChokeFlow(pressureRatio);
    const chokeMargin = ((chokeFlow - correctedFlow) / chokeFlow) * 100;
    
    return {
      compressorSpeed,
      efficiency,
      surgeMargin,
      chokeFlow: chokeMargin
    };
  }

  calculateSpoolTime(
    currentBoost: number,
    targetBoost: number,
    exhaustEnergy: number
  ): number {
    // Simplified spool time calculation
    const boostDelta = targetBoost - currentBoost;
    const spoolRate = exhaustEnergy * 0.001; // Simplified rate
    
    return Math.max(0, boostDelta / spoolRate); // seconds
  }

  calculateTurboEfficiency(
    compressorEfficiency: number,
    turbineEfficiency: number
  ): number {
    // Overall turbo efficiency
    return compressorEfficiency * turbineEfficiency / 100; // percentage
  }

  private initializeCompressorMaps(): void {
    // Simplified compressor map data
    // Format: [flow_rate, pressure_ratio, efficiency]
    this.compressorMap.set('k04', [
      [0.05, 1.2, 55],
      [0.10, 1.5, 65],
      [0.15, 1.8, 72],
      [0.20, 2.1, 75],
      [0.25, 2.4, 74],
      [0.30, 2.7, 70],
      [0.35, 3.0, 65]
    ]);
  }

  private correctFlow(flow: number, boost: number): number {
    // Correct flow to standard conditions
    const boostKpa = boost * 6.895;
    const inletTemp = 25 + 273.15; // Kelvin
    const inletPressure = this.config.atmosphericPressure;
    
    const correctedFlow = flow * Math.sqrt(inletTemp / 298) * (inletPressure / (inletPressure + boostKpa * 1000));
    
    return correctedFlow;
  }

  private estimateSpeed(pressureRatio: number, flow: number): number {
    // Estimate compressor speed in RPM
    // Simplified model based on pressure ratio and flow
    const baseSpeed = 50000; // Base speed at 1:1 pressure ratio
    const speedFactor = Math.pow(pressureRatio, 0.5) * (1 + flow * 2);
    
    return baseSpeed * speedFactor;
  }

  private getCompressorEfficiency(pressureRatio: number, flow: number): number {
    // Interpolate efficiency from compressor map
    const mapData = this.compressorMap.get('k04');
    if (!mapData) return 70; // Default efficiency
    
    // Find nearest points and interpolate
    let maxEfficiency = 0;
    for (const [mapFlow, mapPR, mapEff] of mapData) {
      if (Math.abs(flow - mapFlow) < 0.05 && Math.abs(pressureRatio - mapPR) < 0.2) {
        maxEfficiency = Math.max(maxEfficiency, mapEff);
      }
    }
    
    return maxEfficiency || 70;
  }

  private getSurgeLine(flow: number): number {
    // Simplified surge line calculation
    return 1.1 + flow * 2;
  }

  private getChokeFlow(pressureRatio: number): number {
    // Simplified choke flow calculation
    return 0.4 / Math.sqrt(pressureRatio);
  }

  updateConfig(config: PhysicsConfig): void {
    this.config = config;
    this.emit('configUpdated', config);
  }

  async shutdown(): Promise<void> {
    this.emit('shutdown');
  }
}
