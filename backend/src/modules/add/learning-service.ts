/**
 * ADD Learning Service
 * Subscribes to live telemetry and stores learning data
 */

import { EventEmitter } from 'events';
import { PrismaClient } from '@prisma/client';
import { TelemetryData } from './types';

export interface LearningSession {
  sessionId: string;
  technicianId: string;
  jobId?: string;
  mode: 'LEARN_ONLY' | 'ACTIVE_TUNING';
  startTime: Date;
  sampleCount: number;
  featureCount: number;
  recommendationCount: number;
}

export class LearningService extends EventEmitter {
  private prisma: PrismaClient;
  private activeSession: LearningSession | null = null;
  private subscription: any = null;
  private isSubscribed = false;

  constructor(prisma: PrismaClient) {
    super();
    this.prisma = prisma;
  }

  /**
   * Start a learning session
   */
  async startSession(
    technicianId: string,
    jobId?: string,
    mode: 'LEARN_ONLY' | 'ACTIVE_TUNING' = 'LEARN_ONLY'
  ): Promise<string> {
    // Enforce LEARN_ONLY mode
    if (mode !== 'LEARN_ONLY') {
      throw new Error('Only LEARN_ONLY mode is supported for live learning');
    }

    // Stop any existing session
    if (this.activeSession) {
      await this.stopSession();
    }

    // Create session in database
    const sessionId = `learn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    await this.prisma.addSession.create({
      data: {
        sessionId,
        technicianId,
        jobId,
        mode,
        status: 'ACTIVE'
      }
    });

    // Track active session
    this.activeSession = {
      sessionId,
      technicianId,
      jobId,
      mode,
      startTime: new Date(),
      sampleCount: 0,
      featureCount: 0,
      recommendationCount: 0
    };

    // Subscribe to live telemetry
    await this.subscribeToTelemetry();

    this.emit('sessionStarted', this.activeSession);
    console.log(`ADD Learning session started: ${sessionId}`);

    return sessionId;
  }

  /**
   * Stop the current learning session
   */
  async stopSession(): Promise<void> {
    if (!this.activeSession) {
      return;
    }

    // Unsubscribe from telemetry
    await this.unsubscribeFromTelemetry();

    // Update session in database
    await this.prisma.addSession.update({
      where: { sessionId: this.activeSession.sessionId },
      data: {
        endTime: new Date(),
        status: 'COMPLETED',
        sampleCount: this.activeSession.sampleCount,
        featureCount: this.activeSession.featureCount,
        recommendationCount: this.activeSession.recommendationCount
      }
    });

    const sessionId = this.activeSession.sessionId;
    this.activeSession = null;

    this.emit('sessionStopped', { sessionId });
    console.log(`ADD Learning session stopped: ${sessionId}`);
  }

  /**
   * Get current session info
   */
  getCurrentSession(): LearningSession | null {
    return this.activeSession;
  }

  /**
   * Subscribe to live telemetry stream
   */
  private async subscribeToTelemetry(): Promise<void> {
    if (this.isSubscribed || !this.activeSession) {
      return;
    }

    // In a real implementation, this would connect to the actual telemetry stream
    // For now, we simulate the subscription
    this.subscription = setInterval(() => {
      this.simulateTelemetryData();
    }, 100); // 10Hz sample rate

    this.isSubscribed = true;
    console.log('Subscribed to live telemetry stream');
  }

  /**
   * Unsubscribe from telemetry
   */
  private async unsubscribeFromTelemetry(): Promise<void> {
    if (!this.isSubscribed) {
      return;
    }

    if (this.subscription) {
      clearInterval(this.subscription);
      this.subscription = null;
    }

    this.isSubscribed = false;
    console.log('Unsubscribed from telemetry stream');
  }

  /**
   * Process incoming telemetry data
   */
  private async processTelemetryData(data: TelemetryData): Promise<void> {
    if (!this.activeSession) {
      return;
    }

    try {
      // Store raw sample
      await this.prisma.addRawSample.create({
        data: {
          sessionId: this.activeSession.sessionId,
          rpm: data.engineRpm || 0,
          boost: data.boostPressure || 0,
          afr: data.afr || 14.7,
          timing: data.timingAdvance || 0,
          coolant: data.ect || 80,
          iat: data.iat || 20,
          throttle: data.throttlePosition,
          speed: data.vehicleSpeed,
          source: 'LIVE'
        }
      });

      this.activeSession.sampleCount++;

      // Calculate and store derived features
      await this.calculateDerivedFeatures(data);

      // Generate recommendations (in LEARN_ONLY mode, they're just stored, not applied)
      await this.generateRecommendations(data);

      // Emit progress
      this.emit('progress', {
        sessionId: this.activeSession.sessionId,
        sampleCount: this.activeSession.sampleCount,
        featureCount: this.activeSession.featureCount,
        recommendationCount: this.activeSession.recommendationCount
      });

    } catch (error) {
      console.error('Error processing telemetry:', error);
    }
  }

  /**
   * Calculate derived features from telemetry
   */
  private async calculateDerivedFeatures(data: TelemetryData): Promise<void> {
    if (!this.activeSession) return;

    const features = [
      { name: 'boost_per_rpm', value: (data.boostPressure || 0) / Math.max((data.engineRpm || 1) / 1000, 1), type: 'calculated' },
      { name: 'air_fuel_ratio_deviation', value: Math.abs((data.afr || 14.7) - 14.7), type: 'calculated' },
      { name: 'timing_efficiency', value: (data.timingAdvance || 0) / Math.max((data.engineRpm || 1) / 100, 1), type: 'calculated' },
      { name: 'thermal_efficiency', value: 1 - Math.abs((data.ect || 80) - 80) / 100, type: 'calculated' }
    ];

    for (const feature of features) {
      await this.prisma.addDerivedFeature.create({
        data: {
          sessionId: this.activeSession.sessionId,
          featureName: feature.name,
          featureValue: feature.value,
          featureType: feature.type,
          calculation: `Derived from live telemetry at ${new Date().toISOString()}`
        }
      });

      this.activeSession.featureCount++;
    }
  }

  /**
   * Generate learning recommendations
   */
  private async generateRecommendations(data: TelemetryData): Promise<void> {
    if (!this.activeSession) return;

    const recommendations = [];

    // Simple recommendation logic based on thresholds
    if ((data.boostPressure || 0) > 20) {
      recommendations.push({
        category: 'boost',
        parameterName: 'boost_target',
        currentValue: data.boostPressure || 0,
        recommendedValue: 18,
        changeAmount: -2,
        confidence: 75,
        riskScore: 60,
        rationale: 'High boost pressure detected, recommend reduction for safety',
        evidence: JSON.stringify({ currentBoost: data.boostPressure })
      });
    }

    if ((data.afr || 14.7) < 13.5) {
      recommendations.push({
        category: 'fuel',
        parameterName: 'fuel_trim',
        currentValue: data.afr || 14.7,
        recommendedValue: 14.0,
        changeAmount: 0.5,
        confidence: 80,
        riskScore: 40,
        rationale: 'Running rich, adjust fuel trim for efficiency',
        evidence: JSON.stringify({ currentAFR: data.afr })
      });
    }

    // Store recommendations with write blocking
    for (const rec of recommendations) {
      await this.prisma.addRecommendation.create({
        data: {
          sessionId: this.activeSession.sessionId,
          category: rec.category,
          parameterName: rec.parameterName,
          currentValue: rec.currentValue,
          recommendedValue: rec.recommendedValue,
          changeAmount: rec.changeAmount,
          confidence: rec.confidence,
          riskScore: rec.riskScore,
          expectedImpact: JSON.stringify({
            performance: rec.category === 'boost' ? -5 : 10,
            efficiency: rec.category === 'fuel' ? 15 : 0,
            safety: rec.riskScore > 50 ? -10 : 5
          }),
          rationale: rec.rationale,
          evidence: rec.evidence,
          writeBlocked: true // Always blocked in LEARN_ONLY mode
        }
      });

      this.activeSession.recommendationCount++;
    }
  }

  /**
   * Simulate telemetry data for testing
   */
  private simulateTelemetryData(): void {
    if (!this.activeSession) return;

    const data: TelemetryData = {
      timestamp: Date.now(),
      engineRpm: 1000 + Math.random() * 6000,
      boostPressure: Math.random() * 25,
      afr: 12 + Math.random() * 4,
      timingAdvance: 10 + Math.random() * 30,
      fuelPressure: 40 + Math.random() * 20,
      iat: 20 + Math.random() * 60,
      ect: 70 + Math.random() * 40,
      vehicleSpeed: Math.random() * 120,
      throttlePosition: Math.random() * 100,
      maf: 0 + Math.random() * 300,
      map: 0 + Math.random() * 200,
      lambda: 0.8 + Math.random() * 0.4
    };

    this.processTelemetryData(data);
  }

  /**
   * Get session statistics
   */
  async getSessionStats(sessionId: string): Promise<any> {
    const session = await this.prisma.addSession.findUnique({
      where: { sessionId },
      include: {
        rawSamples: {
          orderBy: { timestamp: 'desc' },
          take: 10
        },
        derivedFeatures: {
          orderBy: { timestamp: 'desc' },
          take: 10
        },
        recommendations: {
          orderBy: { timestamp: 'desc' },
          take: 10
        }
      }
    });

    if (!session) {
      throw new Error('Session not found');
    }

    return {
      session: {
        id: session.id,
        sessionId: session.sessionId,
        mode: session.mode,
        status: session.status,
        startTime: session.startTime,
        endTime: session.endTime,
        sampleCount: session.sampleCount,
        featureCount: session.featureCount,
        recommendationCount: session.recommendationCount
      },
      recentSamples: session.rawSamples,
      recentFeatures: session.derivedFeatures,
      recentRecommendations: session.recommendations
    };
  }

  /**
   * Cleanup service
   */
  async shutdown(): Promise<void> {
    await this.stopSession();
    console.log('Learning service shutdown');
  }
}
