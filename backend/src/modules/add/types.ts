/**
 * ADD Module Types
 * Core types for the Adaptive/AI/Decision subsystem
 */

export interface ADDConfig {
  enabled: boolean;
  learningEnabled: boolean;
  confidenceThreshold: number;
  riskThreshold: number;
  maxRecommendations: number;
}

export interface TelemetryData {
  timestamp: number;
  engineRpm: number;
  boostPressure: number;
  afr: number;
  timingAdvance: number;
  fuelPressure: number;
  iat: number;
  ect: number;
  vehicleSpeed: number;
  throttlePosition: number;
  maf: number;
  map: number;
  lambda: number;
}

export interface DiagnosticData {
  dtcs: string[];
  freezeFrames: Record<string, any>;
  pendingCodes: string[];
  monitorStatus: Record<string, boolean>;
}

export interface SafetyLimits {
  maxBoost: number;
  maxTimingAdvance: number;
  maxFuelPressure: number;
  maxRpm: number;
  minAfr: number;
  maxAfr: number;
  maxIat: number;
  maxEct: number;
}

export interface TuningParameter {
  name: string;
  currentValue: number;
  recommendedValue: number;
  unit: string;
  description: string;
  category: 'fuel' | 'timing' | 'boost' | 'other';
  priority: 'low' | 'medium' | 'high' | 'critical';
}

export interface Recommendation {
  id: string;
  type: 'adjustment' | 'warning' | 'optimization';
  category: 'fuel' | 'timing' | 'boost' | 'safety' | 'diagnostic';
  title: string;
  description: string;
  rationale: string;
  parameters: TuningParameter[];
  confidence: number; // 0-100
  risk: 'low' | 'medium' | 'high' | 'critical';
  expectedImpact: {
    performance: number; // -100 to 100
    efficiency: number; // -100 to 100
    safety: number; // -100 to 100
  };
  requiresUserApproval: boolean;
  canSimulate: boolean;
  estimatedTime?: number; // in seconds
}

export interface DecisionContext {
  vehicleState: {
    isRunning: boolean;
    isWarm: boolean;
    isUnderLoad: boolean;
    isIdling: boolean;
  };
  environmentalConditions: {
    ambientTemp: number;
    humidity: number;
    altitude: number;
  };
  userPreferences: {
    performanceBias: 'economy' | 'balanced' | 'performance';
    riskTolerance: 'conservative' | 'moderate' | 'aggressive';
  };
  sessionHistory: {
    recentChanges: TuningParameter[];
    feedback: Array<{
      recommendationId: string;
      accepted: boolean;
      rating?: number; // 1-5
      notes?: string;
    }>;
  };
}

export interface ADDAnalysis {
  timestamp: number;
  recommendations: Recommendation[];
  overallHealth: number; // 0-100
  performanceScore: number; // 0-100
  efficiencyScore: number; // 0-100
  safetyScore: number; // 0-100
  insights: string[];
  warnings: string[];
  nextActions: string[];
}

export interface LearningData {
  sessionId: string;
  telemetryHistory: TelemetryData[];
  appliedChanges: TuningParameter[];
  outcomes: {
    performanceChange: number;
    efficiencyChange: number;
    safetyEvents: number;
  };
  userFeedback: Array<{
    recommendationId: string;
    accepted: boolean;
    rating: number;
    notes: string;
  }>;
}

export interface ADDProvider {
  name: string;
  analyze: (
    telemetry: TelemetryData,
    diagnostics: DiagnosticData,
    context: DecisionContext
  ) => Promise<Recommendation[]>;
  simulate: (recommendation: Recommendation) => Promise<{
    success: boolean;
    result: any;
    warnings?: string[];
  }>;
}

export interface ADDStrategy {
  name: string;
  description: string;
  applicableConditions: string[];
  providers: string[];
  priority: number;
}

export interface ADDMetrics {
  totalRecommendations: number;
  acceptedRecommendations: number;
  rejectedRecommendations: number;
  averageConfidence: number;
  averageRiskScore: number;
  sessionsAnalyzed: number;
  improvementsMade: number;
  safetyEventsPrevented: number;
}
