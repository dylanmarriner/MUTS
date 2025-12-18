/**
 * Safety Analyzer
 * Evaluates safety implications of current state and recommendations
 */

import { EventEmitter } from 'events';
import { TelemetryData, DiagnosticData, SafetyLimits } from './types';

export interface SafetyAnalysis {
  score: number; // 0-100
  violations: Array<{
    parameter: string;
    value: number;
    limit: number;
    unit: string;
    severity: 'warning' | 'critical';
  }>;
  warnings: string[];
  recommendations: string[];
  riskFactors: Array<{
    factor: string;
    impact: number;
    description: string;
  }>;
}

export class SafetyAnalyzer extends EventEmitter {
  private isInitialized = false;
  private safetyRules: Map<string, any> = new Map();

  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    // Load safety rules and thresholds
    await this.loadSafetyRules();
    
    this.isInitialized = true;
    this.emit('initialized');
  }

  async analyze(
    telemetry: TelemetryData,
    diagnostics: DiagnosticData,
    safetyLimits: SafetyLimits
  ): Promise<SafetyAnalysis> {
    if (!this.isInitialized) {
      throw new Error('SafetyAnalyzer not initialized');
    }

    const violations: any[] = [];
    const warnings: string[] = [];
    const recommendations: string[] = [];
    const riskFactors: any[] = [];
    let totalScore = 100;

    // Check each parameter against safety limits
    const checks = [
      { param: 'Boost Pressure', value: telemetry.boostPressure, limit: safetyLimits.maxBoost, unit: 'PSI' },
      { param: 'Timing Advance', value: telemetry.timingAdvance, limit: safetyLimits.maxTimingAdvance, unit: 'degrees' },
      { param: 'Fuel Pressure', value: telemetry.fuelPressure, limit: safetyLimits.maxFuelPressure, unit: 'PSI' },
      { param: 'Engine RPM', value: telemetry.engineRpm, limit: safetyLimits.maxRpm, unit: 'RPM' },
      { param: 'Intake Air Temp', value: telemetry.iat, limit: safetyLimits.maxIat, unit: '°C' },
      { param: 'Engine Coolant Temp', value: telemetry.ect, limit: safetyLimits.maxEct, unit: '°C' }
    ];

    for (const check of checks) {
      if (check.value > check.limit) {
        const severity = check.value > check.limit * 1.1 ? 'critical' : 'warning';
        violations.push({
          parameter: check.param,
          value: check.value,
          limit: check.limit,
          unit: check.unit,
          severity
        });
        
        totalScore -= severity === 'critical' ? 25 : 10;
      }
    }

    // Check AFR limits
    if (telemetry.afr < safetyLimits.minAfr) {
      violations.push({
        parameter: 'Air-Fuel Ratio',
        value: telemetry.afr,
        limit: safetyLimits.minAfr,
        unit: 'AFR',
        severity: 'critical'
      });
      totalScore -= 25;
    } else if (telemetry.afr > safetyLimits.maxAfr) {
      violations.push({
        parameter: 'Air-Fuel Ratio',
        value: telemetry.afr,
        limit: safetyLimits.maxAfr,
        unit: 'AFR',
        severity: 'warning'
      });
      totalScore -= 10;
    }

    // Analyze risk factors
    if (telemetry.iat > 60) {
      riskFactors.push({
        factor: 'High Intake Temperature',
        impact: 15,
        description: 'Elevated IAT can cause detonation'
      });
      warnings.push('Intake temperature is elevated - consider reducing boost');
      totalScore -= 15;
    }

    if (telemetry.ect > 95) {
      riskFactors.push({
        factor: 'High Engine Temperature',
        impact: 20,
        description: 'High ECT indicates cooling system stress'
      });
      warnings.push('Engine temperature is high - reduce load');
      totalScore -= 20;
    }

    if (telemetry.boostPressure > 20 && telemetry.afr < 13) {
      riskFactors.push({
        factor: 'High Boost with Lean Mixture',
        impact: 30,
        description: 'Dangerous combination for engine health'
      });
      warnings.push('CRITICAL: High boost with lean mixture - immediate action required');
      totalScore -= 30;
    }

    // Check diagnostic codes
    if (diagnostics.dtcs.length > 0) {
      const criticalCodes = diagnostics.dtcs.filter(code => 
        code.startsWith('P0') || code.startsWith('P2')
      );
      
      if (criticalCodes.length > 0) {
        riskFactors.push({
          factor: 'Critical DTCs Present',
          impact: 25,
          description: 'Powertrain issues detected'
        });
        warnings.push(`Critical codes detected: ${criticalCodes.join(', ')}`);
        totalScore -= 25;
      }
    }

    // Generate recommendations
    if (violations.length > 0) {
      recommendations.push('Address safety violations immediately');
      recommendations.push('Consider reducing performance parameters until issues are resolved');
    }

    if (telemetry.boostPressure > 15 && telemetry.iat > 50) {
      recommendations.push('Install intercooler or reduce boost in hot conditions');
    }

    if (telemetry.afr < 12.5) {
      recommendations.push('Check for fuel delivery issues');
    }

    // Ensure score doesn't go below 0
    totalScore = Math.max(0, totalScore);

    const analysis: SafetyAnalysis = {
      score: totalScore,
      violations,
      warnings,
      recommendations,
      riskFactors
    };

    this.emit('analysis', analysis);
    return analysis;
  }

  private async loadSafetyRules(): Promise<void> {
    // Load safety rules from configuration
    this.safetyRules.set('boost', {
      maxPressure: 25,
      pressureRateLimit: 5, // PSI per second
      temperatureCompensation: true
    });

    this.safetyRules.set('fueling', {
      minAfr: 11.0,
      maxAfr: 17.0,
      fuelPressureRange: [40, 80],
      injectorDutyLimit: 90
    });

    this.safetyRules.set('timing', {
      maxAdvance: 35,
      knockRetard: 5,
      temperatureCompensation: true
    });

    this.safetyRules.set('temperature', {
      maxIat: 80,
      maxEct: 110,
      oilTempLimit: 120
    });
  }

  async shutdown(): Promise<void> {
    this.isInitialized = false;
    this.emit('shutdown');
  }
}
