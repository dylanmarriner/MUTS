/**
 * ADD Manager
 * Main orchestrator for the Adaptive/AI/Decision subsystem
 */

import { EventEmitter } from 'events';
import {
  ADDConfig,
  TelemetryData,
  DiagnosticData,
  DecisionContext,
  ADDAnalysis,
  Recommendation,
  ADDProvider,
  ADDStrategy,
  LearningData,
  ADDMetrics,
  SafetyLimits
} from './types';
import { RecommendationEngine } from './recommendation-engine';
import { DecisionHeuristics } from './decision-heuristics';
import { SafetyAnalyzer } from './safety-analyzer';
import { LearningEngine } from './learning-engine';

export class ADDManager extends EventEmitter {
  private config: ADDConfig;
  private providers: Map<string, ADDProvider> = new Map();
  private strategies: Map<string, ADDStrategy> = new Map();
  private recommendationEngine: RecommendationEngine;
  private decisionHeuristics: DecisionHeuristics;
  private safetyAnalyzer: SafetyAnalyzer;
  private learningEngine: LearningEngine;
  private metrics: ADDMetrics;
  private isInitialized = false;

  constructor(config: Partial<ADDConfig> = {}) {
    super();
    
    this.config = {
      enabled: true,
      learningEnabled: true,
      confidenceThreshold: 70,
      riskThreshold: 70,
      maxRecommendations: 10,
      ...config
    };

    this.metrics = {
      totalRecommendations: 0,
      acceptedRecommendations: 0,
      rejectedRecommendations: 0,
      averageConfidence: 0,
      averageRiskScore: 0,
      sessionsAnalyzed: 0,
      improvementsMade: 0,
      safetyEventsPrevented: 0
    };

    // Initialize core components
    this.recommendationEngine = new RecommendationEngine(this.config);
    this.decisionHeuristics = new DecisionHeuristics();
    this.safetyAnalyzer = new SafetyAnalyzer();
    this.learningEngine = new LearningEngine();
  }

  /**
   * Initialize the ADD subsystem
   */
  async initialize(): Promise<void> {
    if (this.isInitialized) {
      return;
    }

    try {
      // Initialize core components
      await this.recommendationEngine.initialize();
      await this.decisionHeuristics.initialize();
      await this.safetyAnalyzer.initialize();
      await this.learningEngine.initialize();

      // Register default providers
      await this.registerDefaultProviders();

      // Load learned data if available
      if (this.config.learningEnabled) {
        await this.learningEngine.loadModel();
      }

      this.isInitialized = true;
      this.emit('initialized');
      console.log('ADD subsystem initialized successfully');
    } catch (error) {
      console.error('Failed to initialize ADD subsystem:', error);
      throw error;
    }
  }

  /**
   * Analyze current vehicle state and generate recommendations
   */
  async analyze(
    telemetry: TelemetryData,
    diagnostics: DiagnosticData,
    context: DecisionContext,
    safetyLimits: SafetyLimits
  ): Promise<ADDAnalysis> {
    if (!this.isInitialized) {
      throw new Error('ADD subsystem not initialized');
    }

    try {
      // Update metrics
      this.metrics.sessionsAnalyzed++;

      // Safety analysis first
      const safetyAnalysis = await this.safetyAnalyzer.analyze(
        telemetry,
        diagnostics,
        safetyLimits
      );

      // Generate recommendations using the recommendation engine
      const recommendations = await this.recommendationEngine.generate(
        telemetry,
        diagnostics,
        context,
        safetyLimits,
        safetyAnalysis
      );

      // Apply decision heuristics to prioritize and filter
      const prioritizedRecommendations = await this.decisionHeuristics.prioritize(
        recommendations,
        context,
        this.config
      );

      // Calculate overall scores
      const analysis: ADDAnalysis = {
        timestamp: Date.now(),
        recommendations: prioritizedRecommendations,
        overallHealth: this.calculateOverallHealth(telemetry, safetyAnalysis),
        performanceScore: this.calculatePerformanceScore(telemetry),
        efficiencyScore: this.calculateEfficiencyScore(telemetry),
        safetyScore: safetyAnalysis.score,
        insights: this.generateInsights(telemetry, diagnostics, prioritizedRecommendations),
        warnings: safetyAnalysis.warnings,
        nextActions: this.generateNextActions(prioritizedRecommendations)
      };

      // Update metrics
      this.updateMetrics(prioritizedRecommendations);

      // Emit analysis complete
      this.emit('analysis', analysis);

      return analysis;
    } catch (error) {
      console.error('ADD analysis failed:', error);
      throw error;
    }
  }

  /**
   * Simulate a recommendation without applying it
   */
  async simulateRecommendation(recommendation: Recommendation): Promise<{
    success: boolean;
    result: any;
    warnings?: string[];
  }> {
    if (!this.isInitialized) {
      throw new Error('ADD subsystem not initialized');
    }

    try {
      // Use the appropriate provider to simulate
      const provider = this.providers.get('default');
      if (!provider) {
        throw new Error('No simulation provider available');
      }

      const result = await provider.simulate(recommendation);
      
      // Emit simulation result
      this.emit('simulated', { recommendation, result });
      
      return result;
    } catch (error) {
      console.error('Simulation failed:', error);
      throw error;
    }
  }

  /**
   * Provide feedback on a recommendation for learning
   */
  async provideFeedback(
    recommendationId: string,
    accepted: boolean,
    rating?: number,
    notes?: string
  ): Promise<void> {
    if (!this.config.learningEnabled) {
      return;
    }

    try {
      await this.learningEngine.recordFeedback({
        recommendationId,
        accepted,
        rating,
        notes,
        timestamp: Date.now()
      });

      // Update metrics
      if (accepted) {
        this.metrics.acceptedRecommendations++;
      } else {
        this.metrics.rejectedRecommendations++;
      }

      this.emit('feedback', { recommendationId, accepted, rating, notes });
    } catch (error) {
      console.error('Failed to record feedback:', error);
    }
  }

  /**
   * Register a new provider
   */
  registerProvider(name: string, provider: ADDProvider): void {
    this.providers.set(name, provider);
    console.log(`Registered ADD provider: ${name}`);
  }

  /**
   * Register a new strategy
   */
  registerStrategy(strategy: ADDStrategy): void {
    this.strategies.set(strategy.name, strategy);
    console.log(`Registered ADD strategy: ${strategy.name}`);
  }

  /**
   * Get current metrics
   */
  getMetrics(): ADDMetrics {
    return { ...this.metrics };
  }

  /**
   * Update configuration
   */
  updateConfig(config: Partial<ADDConfig>): void {
    this.config = { ...this.config, ...config };
    
    // Update component configs
    this.recommendationEngine.updateConfig(this.config);
    this.decisionHeuristics.updateConfig(this.config);
    
    this.emit('configUpdated', this.config);
  }

  /**
   * Shutdown the ADD subsystem
   */
  async shutdown(): Promise<void> {
    if (!this.isInitialized) {
      return;
    }

    try {
      // Save learned data
      if (this.config.learningEnabled) {
        await this.learningEngine.saveModel();
      }

      // Shutdown components
      await this.recommendationEngine.shutdown();
      await this.decisionHeuristics.shutdown();
      await this.safetyAnalyzer.shutdown();
      await this.learningEngine.shutdown();

      this.isInitialized = false;
      this.emit('shutdown');
      console.log('ADD subsystem shutdown complete');
    } catch (error) {
      console.error('Error during ADD shutdown:', error);
      throw error;
    }
  }

  // Private methods

  private async registerDefaultProviders(): Promise<void> {
    // Register built-in providers
    // TODO: Implement default providers for Versa, Cobb, MDS
  }

  private calculateOverallHealth(
    telemetry: TelemetryData,
    safetyAnalysis: any
  ): number {
    // Simple health calculation - can be enhanced
    let health = 100;

    // Check for abnormal values
    if (telemetry.iat > 80) health -= 10;
    if (telemetry.ect > 100) health -= 15;
    if (telemetry.boostPressure > 25) health -= 20;
    if (telemetry.afr < 12 || telemetry.afr > 16) health -= 10;

    // Factor in safety analysis
    health = Math.min(health, safetyAnalysis.score);

    return Math.max(0, health);
  }

  private calculatePerformanceScore(telemetry: TelemetryData): number {
    // Simple performance score based on current conditions
    let score = 50; // Base score

    // Boost pressure contribution
    if (telemetry.boostPressure > 15 && telemetry.boostPressure < 20) {
      score += 20;
    } else if (telemetry.boostPressure >= 20 && telemetry.boostPressure < 25) {
      score += 30;
    } else if (telemetry.boostPressure >= 25) {
      score += 10; // Too much boost is not good
    }

    // AFR contribution
    if (telemetry.afr >= 12.5 && telemetry.afr <= 13.5) {
      score += 20;
    }

    // Timing contribution
    if (telemetry.timingAdvance > 20 && telemetry.timingAdvance < 30) {
      score += 10;
    }

    return Math.min(100, Math.max(0, score));
  }

  private calculateEfficiencyScore(telemetry: TelemetryData): number {
    // Simple efficiency calculation
    let score = 50;

    // AFR efficiency
    if (telemetry.afr >= 14.0 && telemetry.afr <= 15.0) {
      score += 30;
    }

    // Temperature efficiency
    if (telemetry.iat < 50 && telemetry.ect < 90) {
      score += 20;
    }

    return Math.min(100, Math.max(0, score));
  }

  private generateInsights(
    telemetry: TelemetryData,
    diagnostics: DiagnosticData,
    recommendations: Recommendation[]
  ): string[] {
    const insights: string[] = [];

    // Generate insights based on data
    if (telemetry.boostPressure > 20) {
      insights.push('High boost pressure detected - consider checking for boost leaks');
    }

    if (telemetry.afr < 12.5) {
      insights.push('Running rich - may affect fuel economy');
    }

    if (diagnostics.dtcs.length > 0) {
      insights.push(`Active DTCs detected: ${diagnostics.dtcs.join(', ')}`);
    }

    // Add recommendation-based insights
    if (recommendations.length > 0) {
      const highConfidence = recommendations.filter(r => r.confidence > 80);
      if (highConfidence.length > 0) {
        insights.push(`${highConfidence.length} high-confidence recommendations available`);
      }
    }

    return insights;
  }

  private generateNextActions(recommendations: Recommendation[]): string[] {
    const actions: string[] = [];

    // Prioritize critical recommendations
    const critical = recommendations.filter(r => r.risk === 'critical');
    if (critical.length > 0) {
      actions.push('Address critical safety recommendations immediately');
    }

    // High confidence actions
    const highConf = recommendations.filter(r => r.confidence > 85);
    if (highConf.length > 0) {
      actions.push('Review high-confidence tuning recommendations');
    }

    // Simulation suggestions
    const simulatable = recommendations.filter(r => r.canSimulate);
    if (simulatable.length > 0) {
      actions.push('Try simulating recommended changes before applying');
    }

    return actions;
  }

  private updateMetrics(recommendations: Recommendation[]): void {
    this.metrics.totalRecommendations += recommendations.length;

    // Calculate averages
    const totalConf = recommendations.reduce((sum, r) => sum + r.confidence, 0);
    const totalRisk = recommendations.reduce((sum, r) => {
      const riskScore = { low: 25, medium: 50, high: 75, critical: 100 }[r.risk];
      return sum + riskScore;
    }, 0);

    this.metrics.averageConfidence = 
      (this.metrics.averageConfidence + totalConf / recommendations.length) / 2;
    this.metrics.averageRiskScore = 
      (this.metrics.averageRiskScore + totalRisk / recommendations.length) / 2;
  }
}
