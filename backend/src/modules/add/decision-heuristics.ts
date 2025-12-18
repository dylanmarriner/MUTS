/**
 * Decision Heuristics
 * Applies decision-making logic to prioritize and filter recommendations
 */

import { EventEmitter } from 'events';
import { ADDConfig, DecisionContext, Recommendation } from './types';

export class DecisionHeuristics extends EventEmitter {
  private config: ADDConfig;
  private isInitialized = false;

  constructor(config?: Partial<ADDConfig>) {
    super();
    this.config = {
      enabled: true,
      learningEnabled: true,
      confidenceThreshold: 70,
      riskThreshold: 70,
      maxRecommendations: 10,
      ...config
    };
  }

  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    // Load heuristics rules and weights
    await this.loadHeuristics();
    
    this.isInitialized = true;
    this.emit('initialized');
  }

  async prioritize(
    recommendations: Recommendation[],
    context: DecisionContext,
    config: ADDConfig
  ): Promise<Recommendation[]> {
    if (!this.isInitialized) {
      throw new Error('DecisionHeuristics not initialized');
    }

    // Apply filtering rules
    let filtered = this.applyFilters(recommendations, context, config);
    
    // Apply scoring and ranking
    filtered = this.applyScoring(filtered, context);
    
    // Apply context-specific adjustments
    filtered = this.applyContextAdjustments(filtered, context);
    
    // Sort by final score
    filtered.sort((a, b) => (b as any).finalScore - (a as any).finalScore);
    
    // Remove temporary score properties
    return filtered.map(r => {
      const { finalScore, ...cleanRec } = r as any;
      return cleanRec as Recommendation;
    });
  }

  private applyFilters(
    recommendations: Recommendation[],
    context: DecisionContext,
    config: ADDConfig
  ): Recommendation[] {
    return recommendations.filter(rec => {
      // Confidence threshold
      if (rec.confidence < config.confidenceThreshold) {
        return false;
      }
      
      // Risk tolerance filter
      const riskScore = { low: 25, medium: 50, high: 75, critical: 100 }[rec.risk];
      if (riskScore > config.riskThreshold && context.userPreferences.riskTolerance === 'conservative') {
        return false;
      }
      
      // Vehicle state filters
      if (!context.vehicleState.isWarm && rec.category === 'boost') {
        return false; // No boost adjustments when cold
      }
      
      if (context.vehicleState.isIdling && rec.type === 'optimization') {
        return false; // No optimizations at idle
      }
      
      // Performance bias filter
      if (context.userPreferences.performanceBias === 'economy' && 
          rec.expectedImpact.efficiency < 0 && rec.type === 'optimization') {
        return false;
      }
      
      return true;
    });
  }

  private applyScoring(
    recommendations: Recommendation[],
    context: DecisionContext
  ): Recommendation[] {
    return recommendations.map(rec => {
      let score = rec.confidence;
      
      // Risk penalty/bonus based on user tolerance
      const riskMultiplier = {
        conservative: { low: 1.2, medium: 1.0, high: 0.7, critical: 0.3 },
        moderate: { low: 1.1, medium: 1.0, high: 0.9, critical: 0.6 },
        aggressive: { low: 0.9, medium: 1.0, high: 1.1, critical: 0.9 }
      }[context.userPreferences.riskTolerance];
      
      score *= riskMultiplier[rec.risk];
      
      // Performance bias adjustment
      if (context.userPreferences.performanceBias === 'performance') {
        score += rec.expectedImpact.performance * 0.5;
      } else if (context.userPreferences.performanceBias === 'economy') {
        score += rec.expectedImpact.efficiency * 0.5;
      }
      
      // Recent feedback adjustment
      const recentFeedback = context.sessionHistory.feedback
        .filter(f => f.accepted)
        .length;
      score += recentFeedback * 2;
      
      // Priority weighting
      const priorityWeight = {
        low: 0.8,
        medium: 1.0,
        high: 1.2,
        critical: 1.5
      }[rec.parameters[0]?.priority || 'medium'];
      
      score *= priorityWeight;
      
      // Store final score for sorting
      (rec as any).finalScore = score;
      
      return rec;
    });
  }

  private applyContextAdjustments(
    recommendations: Recommendation[],
    context: DecisionContext
  ): Recommendation[] {
    return recommendations.map(rec => {
      // Environmental adjustments
      if (context.environmentalConditions.altitude > 5000 && rec.category === 'fuel') {
        // Lean out fuel at high altitude
        (rec as any).finalScore *= 1.1;
      }
      
      if (context.environmentalConditions.ambientTemp > 30 && rec.category === 'timing') {
        // Reduce timing advance in hot weather
        (rec as any).finalScore *= 0.9;
      }
      
      // Load-based adjustments
      if (context.vehicleState.isUnderLoad && rec.category === 'boost') {
        // Prioritize boost adjustments under load
        (rec as any).finalScore *= 1.2;
      }
      
      return rec;
    });
  }

  private async loadHeuristics(): Promise<void> {
    // Load heuristics from configuration or ML model
    // This could include:
    // - Rule weights
    // - Context importance factors
    // - User preference mappings
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
