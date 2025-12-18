/**
 * Safety Orchestrator - Wraps all tuning engine operations
 * Enforces safety levels, logging, and verification
 */

import { 
  ITuningEngine, 
  SafetyLevel, 
  SAFETY_LEVELS, 
  ApplySession, 
  Changeset, 
  ValidationResult, 
  ApplyResult, 
  SafetySnapshot,
  EngineStatus 
} from './interfaces'
import { EventEmitter } from 'events'
import { randomBytes } from 'crypto'
import { PrismaClient } from '@prisma/client'
import { getSafetyEventQueue } from '../safety-event-queue'

export interface SafetyConfig {
  defaultLevel: SafetyLevel
  requireArming: boolean
  autoRevertMinutes: number | null
  maxConcurrentSessions: number
  requireVerification: boolean
  snapshotInterval: number // milliseconds
}

export class SafetyOrchestrator extends EventEmitter {
  private engines: Map<string, ITuningEngine> = new Map()
  private activeSessions: Map<string, ApplySession> = new Map()
  private safetySnapshots: Map<string, SafetySnapshot[]> = new Map()
  private safetyMonitors: Map<string, NodeJS.Timeout> = new Map()
  private config: SafetyConfig
  private prisma: PrismaClient
  private currentLevel: SafetyLevel = 'SIMULATE'
  private armed: boolean = false
  private eventQueue: any // SafetyEventQueue instance

  constructor(config: Partial<SafetyConfig> = {}, prisma?: PrismaClient) {
    super()
    this.prisma = prisma || new PrismaClient()
    this.eventQueue = getSafetyEventQueue(this.prisma)
    this.config = {
      defaultLevel: 'SIMULATE',
      requireArming: true,
      autoRevertMinutes: 10,
      maxConcurrentSessions: 1,
      requireVerification: true,
      snapshotInterval: 1000,
      ...config
    }
    
    // Start processing the safety event queue
    this.eventQueue.startProcessing()
  }

  /**
   * Emit a safety event through the durable queue
   */
  private async emitSafetyEvent(type: any, data: any): Promise<void> {
    // Emit through EventEmitter for immediate delivery
    this.emit(type, data);
    
    // Also queue for durable delivery
    await this.eventQueue.addEvent(type, data);
  }

  /**
   * Register a tuning engine with the orchestrator
   */
  registerEngine(engine: ITuningEngine): void {
    this.engines.set(engine.engineId, engine)
    this.emitSafetyEvent('engineRegistered', engine.engineId)
  }

  /**
   * Get all registered engines
   */
  getEngines(): ITuningEngine[] {
    return Array.from(this.engines.values())
  }

  /**
   * Get a specific engine by ID
   */
  getEngine(engineId: string): ITuningEngine | undefined {
    return this.engines.get(engineId)
  }

  /**
   * Set the current safety level
   */
  setSafetyLevel(level: SafetyLevel): void {
    const config = SAFETY_LEVELS[level]
    
    if (config.requiresArming && !this.armed) {
      throw new Error(`Safety level ${level} requires arming`)
    }
    
    this.currentLevel = level
    this.emit('safetyLevelChanged', level)
  }

  /**
   * Get current safety level
   */
  getSafetyLevel(): SafetyLevel {
    return this.currentLevel
  }

  /**
   * Arm the system for higher safety levels
   */
  arm(verificationCode: string): boolean {
    // In production, this would validate against a secure system
    // For now, accept any non-empty string
    if (verificationCode && verificationCode.length > 0) {
      this.armed = true
      this.emit('armed')
      return true
    }
    return false
  }

  /**
   * Disarm the system
   */
  disarm(): void {
    this.armed = false
    
    // Auto-revert any active LIVE_APPLY sessions
    for (const [sessionId, session] of this.activeSessions) {
      if (session.mode === 'LIVE_APPLY' && session.status === 'COMPLETED') {
        this.revertLive(sessionId).catch(console.error)
      }
    }
    
    this.emit('disarmed')
  }

  /**
   * Check if system is armed
   */
  isArmed(): boolean {
    return this.armed
  }

  /**
   * Create an apply session with safety checks
   */
  async createApplySession(
    engineId: string,
    vehicleSessionId: string,
    changesetId?: string,
    mode?: SafetyLevel
  ): Promise<ApplySession> {
    const engine = this.engines.get(engineId)
    if (!engine) {
      throw new Error(`Engine ${engineId} not found`)
    }

    const actualMode = mode || this.currentLevel
    const modeConfig = SAFETY_LEVELS[actualMode]

    // Check if mode is supported by engine
    if (actualMode === 'LIVE_APPLY' && !engine.capabilities.supportsLiveApply) {
      throw new Error('LIVE_APPLY not supported by this engine')
    }
    if (actualMode === 'FLASH' && !engine.capabilities.supportsFlash) {
      throw new Error('FLASH not supported by this engine')
    }

    // Check arming requirements
    if (modeConfig.requiresArming && !this.armed) {
      throw new Error(`Mode ${actualMode} requires system to be armed`)
    }

    // Check concurrent sessions
    const activeCount = Array.from(this.activeSessions.values())
      .filter(s => s.status === 'ACTIVE' || s.status === 'COMPLETED').length
    
    if (activeCount >= this.config.maxConcurrentSessions) {
      throw new Error('Maximum concurrent sessions exceeded')
    }

    // Create session through engine
    const session = await engine.startLiveSession(vehicleSessionId, changesetId)
    session.mode = actualMode
    session.armed = false

    // Set expiry for LIVE_APPLY sessions
    if (actualMode === 'LIVE_APPLY' && this.config.autoRevertMinutes) {
      session.expiresAt = new Date(Date.now() + this.config.autoRevertMinutes * 60000)
    }

    this.activeSessions.set(session.id, session)
    this.emit('sessionCreated', session)

    return session
  }

  /**
   * Arm a specific session for execution
   */
  async armSession(sessionId: string, applyToken: string): Promise<boolean> {
    const session = this.activeSessions.get(sessionId)
    if (!session) {
      throw new Error('Session not found')
    }

    if (session.applyToken !== applyToken) {
      throw new Error('Invalid apply token')
    }

    const engine = this.engines.get(session.engineId)
    if (!engine) {
      throw new Error(`Engine ${session.engineId} not found`)
    }

    const success = await engine.armSession(sessionId)
    if (success) {
      session.armed = true
      session.status = 'ARMED'
      this.emit('sessionArmed', session)
    }

    return success
  }

  /**
   * Apply changes with safety verification
   */
  async applyLive(sessionId: string, technicianId?: string, jobId?: string): Promise<ApplyResult> {
    const session = this.activeSessions.get(sessionId)
    if (!session) {
      throw new Error('Session not found')
    }

    if (!session.armed) {
      throw new Error('Session not armed')
    }

    if (session.expiresAt && session.expiresAt < new Date()) {
      throw new Error('Session expired')
    }

    // CRITICAL SAFETY CHECK: Check operator mode for write permissions
    const { operatorMode } = await import('../operator-modes');
    const writeCheck = operatorMode.validateEcuWrite('applyLive');
    
    if (!writeCheck.allowed) {
      throw new Error(`ECU write operations disabled: ${writeCheck.reason}`);
    }

    // CRITICAL: Require technician attribution in non-DEV modes
    if (operatorMode.getCurrentMode() !== 'dev' && !technicianId) {
      throw new Error('Technician attribution required for ECU write operations');
    }

    const engine = this.engines.get(session.engineId)
    if (!engine) {
      throw new Error(`Engine ${session.engineId} not found`)
    }

    // Start safety monitoring
    this.startSafetyMonitoring(sessionId)

    try {
      // Log the write operation if job tracking is available
      if (jobId && technicianId) {
        const { getJobTrackingService } = await import('../job-tracking');
        const jobService = getJobTrackingService(this.prisma);
        await jobService.logTuning(
          jobId,
          technicianId,
          `Applying live tuning changes (${session.changesetId || 'unknown changeset'})`,
          {
            sessionId,
            engineId: session.engineId,
            changesetId: session.changesetId,
            mode: 'LIVE_APPLY',
          }
        );
      }

      // Apply through engine
      const result = await engine.applyLive(sessionId)

      // Verify if required
      if (this.config.requireVerification && !result.ecuVerified) {
        throw new Error('ECU verification failed')
      }

      session.status = 'COMPLETED'
      this.emit('sessionApplied', { session, result })

      return result
    } catch (error) {
      session.status = 'FAILED'
      this.emit('sessionFailed', { session, error })
      throw error
    }
  }

  /**
   * Revert live changes safely
   */
  async revertLive(sessionId: string): Promise<ApplyResult> {
    const session = this.activeSessions.get(sessionId)
    if (!session) {
      throw new Error('Session not found')
    }

    if (session.mode !== 'LIVE_APPLY') {
      throw new Error('Only LIVE_APPLY sessions can be reverted')
    }

    const engine = this.engines.get(session.engineId)
    if (!engine) {
      throw new Error(`Engine ${session.engineId} not found`)
    }

    try {
      const result = await engine.revertLive(sessionId)
      session.status = 'REVERTED'
      this.emit('sessionReverted', { session, result })
      return result
    } catch (error) {
      this.emit('revertFailed', { session, error })
      throw error
    }
  }

  /**
   * Validate changes with safety checks
   */
  async validateChanges(engineId: string, changeset: Changeset): Promise<ValidationResult> {
    const engine = this.engines.get(engineId)
    if (!engine) {
      throw new Error(`Engine ${engineId} not found`)
    }

    // Get engine validation
    const engineResult = await engine.validateChanges(changeset)

    // Apply additional safety orchestrator checks
    const orchestratorResult: ValidationResult = {
      ...engineResult,
      warnings: [
        ...engineResult.warnings,
        this.currentLevel !== 'SIMULATE' ? 
          'Safety level is not SIMULATE - changes will be applied to ECU' :
          'Running in SIMULATE mode - no ECU write will occur'
      ],
      riskScore: Math.max(
        engineResult.riskScore,
        this.currentLevel === 'FLASH' ? 80 : 
        this.currentLevel === 'LIVE_APPLY' ? 40 : 0
      )
    }

    return orchestratorResult
  }

  /**
   * Get all active sessions
   */
  getActiveSessions(): ApplySession[] {
    return Array.from(this.activeSessions.values())
  }

  // Additional methods for WebSocket compatibility
  getCurrentLevel(): SafetyLevel {
    return this.currentLevel
  }

  getActiveSessionsCount(): number {
    return this.activeSessions.size
  }

  /**
   * Get session by ID
   */
  getSession(sessionId: string): ApplySession | undefined {
    return this.activeSessions.get(sessionId)
  }

  /**
   * Get safety snapshots for a session
   */
  getSafetySnapshots(sessionId: string): SafetySnapshot[] {
    return this.safetySnapshots.get(sessionId) || []
  }

  /**
   * Start safety monitoring for a session
   */
  private startSafetyMonitoring(sessionId: string): void {
    const interval = setInterval(async () => {
      const session = this.activeSessions.get(sessionId)
      if (!session || session.status !== 'ACTIVE') {
        clearInterval(interval)
        return
      }

      // Capture safety snapshot
      const snapshot = await this.captureSafetySnapshot(sessionId)
      if (snapshot) {
        const snapshots = this.safetySnapshots.get(sessionId) || []
        snapshots.push(snapshot)
        this.safetySnapshots.set(sessionId, snapshots)

        // Check for safety violations
        this.checkSafetyViolations(sessionId, snapshot)
      }
    }, this.config.snapshotInterval)
  }

  /**
   * Capture current safety snapshot
   */
  private async captureSafetySnapshot(sessionId: string): Promise<SafetySnapshot | null> {
    // This would integrate with telemetry system
    // For now, return mock data
    return {
      sessionId,
      rpm: 2000 + Math.random() * 1000,
      boost: -5 + Math.random() * 20,
      afr: 14.7 + (Math.random() - 0.5) * 2,
      knock: Math.random() * 5,
      coolant: 80 + Math.random() * 40,
      iat: 20 + Math.random() * 60,
      timestamp: new Date()
    }
  }

  /**
   * Check for safety violations in snapshot
   */
  private checkSafetyViolations(sessionId: string, snapshot: SafetySnapshot): void {
    const violations = []

    if (snapshot.knock > 10) {
      violations.push('Excessive knock detected')
    }
    if (snapshot.boost > 25) {
      violations.push('Boost pressure too high')
    }
    if (snapshot.afr < 12) {
      violations.push('AFR too lean')
    }
    if (snapshot.coolant > 110) {
      violations.push('Coolant temperature too high')
    }

    if (violations.length > 0) {
      this.emit('safetyViolation', { sessionId, violations, snapshot })
      
      // Auto-revert on critical violations
      if (snapshot.knock > 20 || snapshot.boost > 30) {
        this.revertLive(sessionId).catch(console.error)
      }
    }
  }

  /**
   * Get overall system status
   */
  async getSystemStatus(): Promise<{
    safetyLevel: SafetyLevel
    armed: boolean
    activeSessions: number
    engines: EngineStatus[]
    warnings: string[]
  }> {
    const engines = await Promise.all(
      Array.from(this.engines.values()).map(e => e.status())
    )

    return {
      safetyLevel: this.currentLevel,
      armed: this.armed,
      activeSessions: this.activeSessions.size,
      engines,
      warnings: this.currentLevel !== 'SIMULATE' && !this.armed ? 
        ['System not armed - higher safety levels unavailable'] : []
    }
  }
}
