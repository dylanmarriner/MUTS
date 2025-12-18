/**
 * Learning Engine
 * Learns from user feedback and outcomes to improve recommendations
 */

import { EventEmitter } from 'events';
import { 
  LearningData, 
  Recommendation, 
  TelemetryData, 
  TuningParameter,
  DecisionContext 
} from './types';

export interface FeedbackData {
  recommendationId: string;
  accepted: boolean;
  rating?: number; // 1-5
  notes?: string;
  timestamp: number;
}

export interface LearningModel {
  userPreferences: {
    riskTolerance: number; // 0-100
    performanceBias: number; // -1 (economy) to 1 (performance)
    feedbackWeight: number; // How much to weight user feedback
  };
  patternWeights: Map<string, number>;
  successPatterns: Array<{
    pattern: string;
    confidence: number;
    outcomes: number[];
  }>;
}

export class LearningEngine extends EventEmitter {
  private isInitialized = false;
  private model: LearningModel;
  private feedbackHistory: FeedbackData[] = [];
  private learningData: LearningData[] = [];
  private modelPath = './data/add-learning-model.json';

  constructor() {
    super();
    
    this.model = {
      userPreferences: {
        riskTolerance: 50,
        performanceBias: 0,
        feedbackWeight: 0.7
      },
      patternWeights: new Map(),
      successPatterns: []
    };
  }

  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    // Load existing model if available
    await this.loadModel();
    
    this.isInitialized = true;
    this.emit('initialized');
  }

  async recordFeedback(feedback: FeedbackData): Promise<void> {
    if (!this.isInitialized) {
      throw new Error('LearningEngine not initialized');
    }

    this.feedbackHistory.push(feedback);
    
    // Update user preferences based on feedback
    this.updateUserPreferences(feedback);
    
    // Update pattern weights
    this.updatePatternWeights(feedback);
    
    // Emit feedback recorded
    this.emit('feedbackRecorded', feedback);
  }

  async recordSession(session: LearningData): Promise<void> {
    this.learningData.push(session);
    
    // Analyze session outcomes
    await this.analyzeSessionOutcomes(session);
    
    // Emit session recorded
    this.emit('sessionRecorded', session);
  }

  async getRecommendationConfidence(
    recommendation: Recommendation,
    context: DecisionContext,
    telemetryHistory: TelemetryData[]
  ): Promise<number> {
    let confidence = recommendation.confidence;
    
    // Apply learned adjustments
    const pattern = this.extractPattern(recommendation, context);
    const patternWeight = this.model.patternWeights.get(pattern) || 1.0;
    confidence *= patternWeight;
    
    // Adjust based on user feedback history
    const similarRecommendations = this.findSimilarRecommendations(recommendation);
    if (similarRecommendations.length > 0) {
      const avgRating = similarRecommendations.reduce((sum, r) => 
        sum + (r.rating || 3), 0) / similarRecommendations.length;
      
      // Adjust confidence based on historical ratings
      confidence *= (avgRating / 3);
    }
    
    // Consider user preferences
    if (this.model.userPreferences.performanceBias > 0.5 && 
        recommendation.expectedImpact.performance > 0) {
      confidence *= 1.1;
    }
    
    if (this.model.userPreferences.performanceBias < -0.5 && 
        recommendation.expectedImpact.efficiency > 0) {
      confidence *= 1.1;
    }
    
    // Risk tolerance adjustment
    const riskScore = { low: 25, medium: 50, high: 75, critical: 100 }[recommendation.risk];
    if (riskScore > this.model.userPreferences.riskTolerance) {
      confidence *= 0.8;
    }
    
    return Math.min(100, Math.max(0, confidence));
  }

  async saveModel(): Promise<void> {
    try {
      const modelData = {
        model: this.model,
        feedbackHistory: this.feedbackHistory.slice(-1000), // Keep last 1000
        learningData: this.learningData.slice(-100), // Keep last 100 sessions
        timestamp: Date.now()
      };
      
      // In a real implementation, save to file/database
      console.log('Learning model saved');
      this.emit('modelSaved', modelData);
    } catch (error) {
      console.error('Failed to save learning model:', error);
    }
  }

  async loadModel(): Promise<void> {
    try {
      // In a real implementation, load from file/database
      console.log('Learning model loaded');
      this.emit('modelLoaded', this.model);
    } catch (error) {
      console.log('No existing model found, starting fresh');
    }
  }

  private updateUserPreferences(feedback: FeedbackData): void {
    const weight = this.model.userPreferences.feedbackWeight;
    
    // Update risk tolerance based on accepted/rejected risky recommendations
    if (feedback.rating) {
      const riskAdjustment = (feedback.rating - 3) * 2 * weight;
      this.model.userPreferences.riskTolerance = 
        Math.max(0, Math.min(100, 
          this.model.userPreferences.riskTolerance + riskAdjustment));
    }
    
    // Update performance bias based on feedback patterns
    // This would need more context about the recommendation type
  }

  private updatePatternWeights(feedback: FeedbackData): void {
    // Extract pattern from feedback (would need recommendation context)
    // For now, use a simple pattern based on acceptance rate
    const pattern = feedback.accepted ? 'accepted' : 'rejected';
    const currentWeight = this.model.patternWeights.get(pattern) || 1.0;
    
    // Gradually adjust weight
    const adjustment = feedback.accepted ? 0.01 : -0.01;
    const newWeight = Math.max(0.1, Math.min(2.0, currentWeight + adjustment));
    
    this.model.patternWeights.set(pattern, newWeight);
  }

  private async analyzeSessionOutcomes(session: LearningData): Promise<void> {
    // Analyze what worked and what didn't
    if (session.outcomes.performanceChange > 0) {
      // Performance improved - learn from these changes
      for (const change of session.appliedChanges) {
        const pattern = `${change.category}-${change.name}`;
        const currentWeight = this.model.patternWeights.get(pattern) || 1.0;
        this.model.patternWeights.set(pattern, Math.min(2.0, currentWeight * 1.05));
      }
    }
    
    // Check user feedback correlation with outcomes
    for (const feedback of session.userFeedback) {
      if (feedback.accepted && feedback.rating && feedback.rating >= 4) {
        // User liked it and it worked well
        const pattern = `positive-${feedback.recommendationId}`;
        this.model.patternWeights.set(pattern, 1.2);
      }
    }
  }

  private extractPattern(recommendation: Recommendation, context: DecisionContext): string {
    // Create a pattern key based on recommendation characteristics
    const parts = [
      recommendation.category,
      recommendation.type,
      recommendation.risk,
      context.userPreferences.performanceBias,
      context.vehicleState.isUnderLoad ? 'load' : 'noload'
    ];
    
    return parts.join('-');
  }

  private findSimilarRecommendations(recommendation: Recommendation): FeedbackData[] {
    // Find feedback for similar recommendations
    return this.feedbackHistory.filter(f => {
      // In a real implementation, this would be more sophisticated
      // For now, just return recent feedback
      return Date.now() - f.timestamp < 7 * 24 * 60 * 60 * 1000; // Last 7 days
    });
  }

  async shutdown(): Promise<void> {
    // Save model before shutting down
    await this.saveModel();
    
    this.isInitialized = false;
    this.emit('shutdown');
  }

  // Analytics methods
  
  getLearningStats(): {
    totalFeedback: number;
    acceptanceRate: number;
    averageRating: number;
    sessionsAnalyzed: number;
    topPatterns: Array<{ pattern: string; weight: number }>;
  } {
    const totalFeedback = this.feedbackHistory.length;
    const acceptedFeedback = this.feedbackHistory.filter(f => f.accepted).length;
    const acceptanceRate = totalFeedback > 0 ? (acceptedFeedback / totalFeedback) * 100 : 0;
    
    const ratingsWithValues = this.feedbackHistory.filter(f => f.rating !== undefined);
    const averageRating = ratingsWithValues.length > 0 
      ? ratingsWithValues.reduce((sum, f) => sum + (f.rating || 0), 0) / ratingsWithValues.length
      : 0;
    
    const topPatterns = Array.from(this.model.patternWeights.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([pattern, weight]) => ({ pattern, weight }));
    
    return {
      totalFeedback,
      acceptanceRate,
      averageRating,
      sessionsAnalyzed: this.learningData.length,
      topPatterns
    };
  }

  resetLearning(): void {
    this.model = {
      userPreferences: {
        riskTolerance: 50,
        performanceBias: 0,
        feedbackWeight: 0.7
      },
      patternWeights: new Map(),
      successPatterns: []
    };
    this.feedbackHistory = [];
    this.learningData = [];
    
    this.emit('reset');
  }
}
