/**
 * Recommendation Engine
 * Generates tuning recommendations based on telemetry, diagnostics, and context
 */

import { EventEmitter } from 'events';
import {
  ADDConfig,
  TelemetryData,
  DiagnosticData,
  DecisionContext,
  Recommendation,
  TuningParameter,
  SafetyLimits,
  ADDProvider
} from './types';

export class RecommendationEngine extends EventEmitter {
  private config: ADDConfig;
  private providers: Map<string, ADDProvider> = new Map();
  private isInitialized = false;

  constructor(config: ADDConfig) {
    super();
    this.config = config;
  }

  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    // Initialize built-in recommendation algorithms
    await this.initializeBuiltinProviders();
    
    this.isInitialized = true;
    this.emit('initialized');
  }

  async generate(
    telemetry: TelemetryData,
    diagnostics: DiagnosticData,
    context: DecisionContext,
    safetyLimits: SafetyLimits,
    safetyAnalysis: any
  ): Promise<Recommendation[]> {
    if (!this.isInitialized) {
      throw new Error('RecommendationEngine not initialized');
    }

    const recommendations: Recommendation[] = [];

    // Generate recommendations from different analysis modules
    recommendations.push(
      ...await this.analyzeFueling(telemetry, context, safetyLimits),
      ...await this.analyzeTiming(telemetry, context, safetyLimits),
      ...await this.analyzeBoost(telemetry, context, safetyLimits),
      ...await this.analyzeDiagnostics(diagnostics, telemetry),
      ...await this.analyzeSafety(safetyAnalysis)
    );

    // Sort by confidence and priority
    recommendations.sort((a, b) => {
      // First by risk (critical first)
      const riskOrder = { critical: 0, high: 1, medium: 2, low: 3 };
      if (riskOrder[a.risk] !== riskOrder[b.risk]) {
        return riskOrder[a.risk] - riskOrder[b.risk];
      }
      
      // Then by confidence
      return b.confidence - a.confidence;
    });

    // Limit to max recommendations
    return recommendations.slice(0, this.config.maxRecommendations);
  }

  private async initializeBuiltinProviders(): Promise<void> {
    // Register built-in providers for different tuning strategies
    this.providers.set('fuel', new FuelingProvider());
    this.providers.set('timing', new TimingProvider());
    this.providers.set('boost', new BoostProvider());
    this.providers.set('diagnostic', new DiagnosticProvider());
  }

  private async analyzeFueling(
    telemetry: TelemetryData,
    context: DecisionContext,
    safetyLimits: SafetyLimits
  ): Promise<Recommendation[]> {
    const recommendations: Recommendation[] = [];

    // Check AFR
    if (telemetry.afr < safetyLimits.minAfr) {
      recommendations.push({
        id: `fuel-lean-${Date.now()}`,
        type: 'warning',
        category: 'fuel',
        title: 'Running Too Lean',
        description: 'Air-Fuel Ratio is below safe limits',
        rationale: `Current AFR of ${telemetry.afr} is below the minimum safe value of ${safetyLimits.minAfr}`,
        parameters: [{
          name: 'Fuel Pressure',
          currentValue: telemetry.fuelPressure,
          recommendedValue: Math.min(telemetry.fuelPressure * 1.1, safetyLimits.maxFuelPressure),
          unit: 'PSI',
          description: 'Increase fuel pressure to enrich mixture',
          category: 'fuel',
          priority: 'critical'
        }],
        confidence: 90,
        risk: 'critical',
        expectedImpact: {
          performance: -10,
          efficiency: -20,
          safety: 50
        },
        requiresUserApproval: true,
        canSimulate: true
      });
    } else if (telemetry.afr > safetyLimits.maxAfr) {
      recommendations.push({
        id: `fuel-rich-${Date.now()}`,
        type: 'optimization',
        category: 'fuel',
        title: 'Running Rich',
        description: 'Air-Fuel Ratio is richer than optimal',
        rationale: `Current AFR of ${telemetry.afr} is above the optimal range`,
        parameters: [{
          name: 'Fuel Pressure',
          currentValue: telemetry.fuelPressure,
          recommendedValue: Math.max(telemetry.fuelPressure * 0.95, 40),
          unit: 'PSI',
          description: 'Reduce fuel pressure for better efficiency',
          category: 'fuel',
          priority: 'medium'
        }],
        confidence: 75,
        risk: 'low',
        expectedImpact: {
          performance: 5,
          efficiency: 15,
          safety: 0
        },
        requiresUserApproval: true,
        canSimulate: true
      });
    }

    return recommendations;
  }

  private async analyzeTiming(
    telemetry: TelemetryData,
    context: DecisionContext,
    safetyLimits: SafetyLimits
  ): Promise<Recommendation[]> {
    const recommendations: Recommendation[] = [];

    // Check timing advance
    if (telemetry.timingAdvance > safetyLimits.maxTimingAdvance) {
      recommendations.push({
        id: `timing-advance-${Date.now()}`,
        type: 'warning',
        category: 'timing',
        title: 'Excessive Timing Advance',
        description: 'Timing advance is approaching safety limits',
        rationale: `Current timing of ${telemetry.timingAdvance}° is near the maximum of ${safetyLimits.maxTimingAdvance}°`,
        parameters: [{
          name: 'Timing Advance',
          currentValue: telemetry.timingAdvance,
          recommendedValue: safetyLimits.maxTimingAdvance - 2,
          unit: 'degrees',
          description: 'Reduce timing to prevent knock',
          category: 'timing',
          priority: 'high'
        }],
        confidence: 85,
        risk: 'high',
        expectedImpact: {
          performance: -5,
          efficiency: -5,
          safety: 40
        },
        requiresUserApproval: true,
        canSimulate: true
      });
    } else if (context.userPreferences.performanceBias === 'performance' && 
               telemetry.timingAdvance < safetyLimits.maxTimingAdvance - 5) {
      recommendations.push({
        id: `timing-optimize-${Date.now()}`,
        type: 'optimization',
        category: 'timing',
        title: 'Optimize Timing',
        description: 'Increase timing for better performance',
        rationale: 'Timing can be safely increased for better power output',
        parameters: [{
          name: 'Timing Advance',
          currentValue: telemetry.timingAdvance,
          recommendedValue: Math.min(telemetry.timingAdvance + 2, safetyLimits.maxTimingAdvance - 3),
          unit: 'degrees',
          description: 'Advance timing for improved performance',
          category: 'timing',
          priority: 'medium'
        }],
        confidence: 70,
        risk: 'low',
        expectedImpact: {
          performance: 10,
          efficiency: 0,
          safety: -5
        },
        requiresUserApproval: true,
        canSimulate: true
      });
    }

    return recommendations;
  }

  private async analyzeBoost(
    telemetry: TelemetryData,
    context: DecisionContext,
    safetyLimits: SafetyLimits
  ): Promise<Recommendation[]> {
    const recommendations: Recommendation[] = [];

    // Check boost pressure
    if (telemetry.boostPressure > safetyLimits.maxBoost) {
      recommendations.push({
        id: `boost-overlimit-${Date.now()}`,
        type: 'warning',
        category: 'boost',
        title: 'Boost Pressure Exceeded',
        description: 'Boost pressure is above safety limits',
        rationale: `Current boost of ${telemetry.boostPressure} PSI exceeds maximum of ${safetyLimits.maxBoost} PSI`,
        parameters: [{
          name: 'Wastegate Duty',
          currentValue: 0, // Would be read from ECU
          recommendedValue: 80,
          unit: '%',
          description: 'Increase wastegate duty to reduce boost',
          category: 'boost',
          priority: 'critical'
        }],
        confidence: 95,
        risk: 'critical',
        expectedImpact: {
          performance: -20,
          efficiency: -10,
          safety: 60
        },
        requiresUserApproval: true,
        canSimulate: true
      });
    }

    return recommendations;
  }

  private async analyzeDiagnostics(
    diagnostics: DiagnosticData,
    telemetry: TelemetryData
  ): Promise<Recommendation[]> {
    const recommendations: Recommendation[] = [];

    // Check for DTCs
    if (diagnostics.dtcs.length > 0) {
      recommendations.push({
        id: `dtc-warning-${Date.now()}`,
        type: 'warning',
        category: 'diagnostic',
        title: 'Diagnostic Trouble Codes Detected',
        description: `${diagnostics.dtcs.length} DTC(s) require attention`,
        rationale: `Active codes: ${diagnostics.dtcs.join(', ')}`,
        parameters: [],
        confidence: 100,
        risk: 'medium',
        expectedImpact: {
          performance: -10,
          efficiency: -5,
          safety: -20
        },
        requiresUserApproval: false,
        canSimulate: false
      });
    }

    return recommendations;
  }

  private async analyzeSafety(safetyAnalysis: any): Promise<Recommendation[]> {
    const recommendations: Recommendation[] = [];

    if (safetyAnalysis.violations && safetyAnalysis.violations.length > 0) {
      recommendations.push({
        id: `safety-violation-${Date.now()}`,
        type: 'warning',
        category: 'safety',
        title: 'Safety Violations Detected',
        description: 'Parameters exceed safety limits',
        rationale: `${safetyAnalysis.violations.length} safety violation(s) detected`,
        parameters: safetyAnalysis.violations.map((v: any) => ({
          name: v.parameter,
          currentValue: v.value,
          recommendedValue: v.limit,
          unit: v.unit || '',
          description: `Adjust ${v.parameter} to safe level`,
          category: 'other' as const,
          priority: 'critical' as const
        })),
        confidence: 100,
        risk: 'critical',
        expectedImpact: {
          performance: -15,
          efficiency: -10,
          safety: 50
        },
        requiresUserApproval: true,
        canSimulate: true
      });
    }

    return recommendations;
  }

  async shutdown(): Promise<void> {
    this.isInitialized = false;
    this.emit('shutdown');
  }

  updateConfig(config: ADDConfig): void {
    this.config = { ...this.config, ...config };
    this.emit('configUpdated', config);
  }
}

// Built-in provider implementations
class FuelingProvider implements ADDProvider {
  name = 'fuel';

  async analyze(
    telemetry: TelemetryData,
    diagnostics: DiagnosticData,
    context: DecisionContext
  ): Promise<Recommendation[]> {
    // Implementation would be moved from analyzeFueling method
    return [];
  }

  async simulate(recommendation: Recommendation): Promise<{
    success: boolean;
    result: any;
    warnings?: string[];
  }> {
    // Simulate fueling changes
    return {
      success: true,
      result: {
        newAfr: 13.5,
        estimatedHpGain: 5,
        estimatedFuelEconomyChange: -0.5
      }
    };
  }
}

class TimingProvider implements ADDProvider {
  name = 'timing';

  async analyze(
    telemetry: TelemetryData,
    diagnostics: DiagnosticData,
    context: DecisionContext
  ): Promise<Recommendation[]> {
    return [];
  }

  async simulate(recommendation: Recommendation): Promise<{
    success: boolean;
    result: any;
    warnings?: string[];
  }> {
    return {
      success: true,
      result: {
        estimatedHpGain: 8,
        estimatedKnockRisk: 5
      }
    };
  }
}

class BoostProvider implements ADDProvider {
  name = 'boost';

  async analyze(
    telemetry: TelemetryData,
    diagnostics: DiagnosticData,
    context: DecisionContext
  ): Promise<Recommendation[]> {
    return [];
  }

  async simulate(recommendation: Recommendation): Promise<{
    success: boolean;
    result: any;
    warnings?: string[];
  }> {
    return {
      success: true,
      result: {
        newBoostPressure: 18,
        estimatedHpGain: 15,
        estimatedStressIncrease: 10
      }
    };
  }
}

class DiagnosticProvider implements ADDProvider {
  name = 'diagnostic';

  async analyze(
    telemetry: TelemetryData,
    diagnostics: DiagnosticData,
    context: DecisionContext
  ): Promise<Recommendation[]> {
    return [];
  }

  async simulate(recommendation: Recommendation): Promise<{
    success: boolean;
    result: any;
    warnings?: string[];
  }> {
    return {
      success: true,
      result: {
        codesCleared: true,
        systemsAffected: ['engine', 'transmission']
      }
    };
  }
}
