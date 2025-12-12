/**
 * ADD (Adaptive/AI/Decision) Module
 * Core AI subsystem for MUTS - responsible for:
 * - AI tuner logic
 * - Adaptive recommendations
 * - Decision heuristics
 * Safety-aware tuning suggestions
 */

export { ADDManager } from './add-manager';
export { RecommendationEngine } from './recommendation-engine';
export { DecisionHeuristics } from './decision-heuristics';
export { SafetyAnalyzer } from './safety-analyzer';
export { LearningEngine } from './learning-engine';
export * from './types';

// Module initialization
export const initializeADD = async () => {
  // Initialize ADD subsystem
  console.log('Initializing ADD subsystem...');
  // TODO: Load models, initialize weights, etc.
};
