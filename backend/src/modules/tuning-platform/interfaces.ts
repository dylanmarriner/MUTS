/**
 * Unified Tuning Platform - Engine Interfaces
 * Defines the common interface that all tuning engines must implement
 */

export interface MapDefinition {
  id: string
  name: string
  type: string
  description?: string
  address?: string
  size?: number
  dataType: string
  units?: string
  minValue?: number
  maxValue?: number
  xAxis?: number[]
  yAxis?: number[]
  category?: string
  isRuntimeAdjustable?: boolean
  metadata?: Record<string, any>
}

export interface MapData {
  mapId: string
  values: any[][]
  metadata?: Record<string, any>
}

export interface MapChange {
  mapId: string
  xIndex?: number
  yIndex?: number
  oldValue?: number
  newValue: number
  reason?: string
  timestamp: Date
}

export interface Changeset {
  id: string
  profileId: string
  engineId: string
  author: string
  notes?: string
  changes: MapChange[]
  createdAt: Date
  metadata?: Record<string, any>
}

export interface ValidationResult {
  valid: boolean
  riskScore: number // 0-100
  warnings: string[]
  errors: string[]
  safetyViolations: string[]
  recommendations?: string[]
}

export interface SimulationResult {
  changesetId: string
  effects: {
    estimatedPowerGain?: number
    estimatedTorqueGain?: number
    riskLevel: 'LOW' | 'MEDIUM' | 'HIGH'
  }
  warnings: string[]
  recommendations: string[]
}

export interface ApplySession {
  id: string
  engineId: string
  vehicleSessionId: string
  changesetId?: string
  mode: 'SIMULATE' | 'LIVE_APPLY' | 'FLASH'
  status: 'PENDING' | 'ARMED' | 'ACTIVE' | 'COMPLETED' | 'REVERTED' | 'FAILED'
  armed: boolean
  expiresAt?: Date
  createdAt: Date
  updatedAt: Date
  applyToken?: string
  revertReason?: string
  metadata?: Record<string, any>
}

export interface ApplyResult {
  success: boolean
  ecuVerified: boolean
  appliedChanges: number
  failedChanges: string[]
  verificationErrors?: string[]
  message: string
}

export interface FlashJob {
  id: string
  engineId: string
  sessionId: string
  state: 'PREPARED' | 'VALIDATING' | 'FLASHING' | 'VERIFYING' | 'COMPLETED' | 'FAILED' | 'ABORTED'
  progress: number // 0-100
  checksumOk: boolean
  validationOk: boolean
  errorMessage?: string
  createdAt: Date
  updatedAt: Date
}

export interface SafetySnapshot {
  sessionId: string
  rpm: number
  boost: number
  afr: number
  knock: number
  coolant: number
  iat: number
  timestamp: Date
  throttle?: number
  speed?: number
  oilPressure?: number
}

export interface EngineCapabilities {
  engineId: string
  name: string
  version: string
  supportedModes: ('SIMULATE' | 'LIVE_APPLY' | 'FLASH')[]
  supportsLiveApply: boolean
  supportsFlash: boolean
  supportsSimulation: boolean
  requiresArming: boolean
  maxMapSize?: number
  supportedMapTypes: string[]
  customActions?: EngineAction[]
}

export interface EngineAction {
  id: string
  name: string
  description: string
  category: string
  parameters: Record<string, any>
  requiresSafetyLevel: 'SIMULATE' | 'LIVE_APPLY' | 'FLASH'
}

export interface EngineStatus {
  engineId: string
  connected: boolean
  vehicleConnected: boolean
  currentSession?: string
  safetyLevel: 'SIMULATE' | 'LIVE_APPLY' | 'FLASH'
  armed: boolean
  lastActivity: Date
  errors: string[]
  warnings: string[]
}

/**
 * Main TuningEngine interface that all engines must implement
 */
export interface ITuningEngine {
  // Engine identification
  readonly engineId: string
  readonly name: string
  readonly version: string
  readonly capabilities: EngineCapabilities

  // Connection and discovery
  connect(): Promise<boolean>
  disconnect(): Promise<void>
  discoverDefinitions(): Promise<MapDefinition[]>
  status(): Promise<EngineStatus>

  // Map operations
  listMaps(profileId: string): Promise<MapDefinition[]>
  getMap(mapId: string): Promise<MapData>
  updateMap(mapId: string, payload: MapData): Promise<boolean>

  // Changeset operations
  createChangeset(profileId: string, changes: MapChange[], author: string, notes?: string): Promise<Changeset>
  getChangeset(changesetId: string): Promise<Changeset | null>
  listChangesets(profileId: string): Promise<Changeset[]>

  // Validation and simulation
  validateChanges(changeset: Changeset): Promise<ValidationResult>
  simulate(changeset: Changeset): Promise<SimulationResult>

  // Patch operations
  buildPatch(changeset: Changeset): Promise<Buffer>
  validatePatch(patchData: Buffer, originalRom: Buffer): Promise<ValidationResult>
  
  // Additional methods for WebSocket compatibility
  getCapabilities(): EngineCapabilities
  buildFlashImage(profileId: string): Promise<Buffer>

  // Live apply operations
  startLiveSession(vehicleSessionId: string, changesetId?: string): Promise<ApplySession>
  armSession(sessionId: string): Promise<boolean>
  applyLive(sessionId: string): Promise<ApplyResult>
  revertLive(sessionId: string): Promise<ApplyResult>

  // Flash operations
  prepareFlash(profileId: string, changesetId?: string): Promise<FlashJob>
  executeFlash(jobId: string): Promise<void>
  abortFlash(jobId: string): Promise<void>

  // Engine-specific actions (for MDS special requirements)
  executeAction(actionId: string, parameters: Record<string, any>): Promise<any>
  listActions(): Promise<EngineAction[]>

  // Telemetry and monitoring
  subscribeTelemetry(callback: (data: any) => void): void
  unsubscribeTelemetry(): void
}

/**
 * Safety levels configuration
 */
export const SAFETY_LEVELS = {
  SIMULATE: {
    name: 'Simulate Mode',
    description: 'No ECU write - compute changes only',
    allowsWrite: false,
    requiresArming: false,
    timeoutMinutes: null,
    color: 'blue',
    icon: 'Activity'
  },
  LIVE_APPLY: {
    name: 'Live Apply',
    description: 'Session-based reversible changes',
    allowsWrite: true,
    requiresArming: true,
    timeoutMinutes: 10,
    color: 'orange',
    icon: 'Zap'
  },
  FLASH: {
    name: 'Flash Mode',
    description: 'Persistent ROM write',
    allowsWrite: true,
    requiresArming: true,
    timeoutMinutes: null,
    color: 'red',
    icon: 'Shield'
  }
} as const

export type SafetyLevel = keyof typeof SAFETY_LEVELS
