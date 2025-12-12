/**
 * Global Application Store
 * Manages connection, safety, and telemetry state across all tabs
 */

import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';

// Type definitions
export type SafetyLevel = 'ReadOnly' | 'Simulate' | 'LiveApply' | 'Flash';
export type ConnectionStatus = 'NO_INTERFACE_CONNECTED' | 'CONNECTING' | 'CONNECTED' | 'DISCONNECTING' | 'ERROR';

export interface InterfaceInfo {
  id: string;
  name: string;
  interfaceType: 'SocketCAN' | 'J2534' | 'CANALyst' | 'Vector' | 'Custom';
  capabilities: string[];
  isAvailable: boolean;
}

export interface TelemetryData {
  timestamp: Date;
  signals: Record<string, number>;
  metadata: {
    source: string;
    sampleRate: number;
    quality: 'good' | 'fair' | 'poor' | 'invalid';
  };
}

export interface SafetyViolation {
  parameter: string;
  value: number;
  limit: number;
  severity: 'Warning' | 'Critical';
}

export interface SafetyState {
  armed: boolean;
  level: SafetyLevel;
  timeRemaining?: number;
  violations: SafetyViolation[];
}

export interface SessionInfo {
  id: string;
  type: 'connection' | 'diagnostic' | 'tuning' | 'flash';
  status: 'active' | 'idle' | 'error';
  startTime: Date;
  endTime?: Date;
  metadata: Record<string, any>;
}

interface AppStore {
  // Connection state
  connectionStatus: ConnectionStatus;
  connectedInterface: InterfaceInfo | null;
  availableInterfaces: InterfaceInfo[];
  currentSession: SessionInfo | null;
  sessions: SessionInfo[];

  // Safety state
  safetyState: SafetyState;
  safetyArmed: boolean;
  safetyLevel: SafetyLevel;

  // Telemetry state
  isStreaming: boolean;
  currentTelemetry: TelemetryData | null;
  telemetryHistory: TelemetryData[];
  maxHistorySize: number;

  // Vehicle info
  vehicleInfo: {
    vin?: string;
    make?: string;
    model?: string;
    year?: number;
    ecuType?: string;
    calibrationId?: string;
  };

  // Actions
  setConnectionStatus: (status: ConnectionStatus) => void;
  setConnectedInterface: (interface: InterfaceInfo | null) => void;
  setAvailableInterfaces: (interfaces: InterfaceInfo[]) => void;
  setCurrentSession: (session: SessionInfo | null) => void;
  addSession: (session: SessionInfo) => void;
  updateSession: (id: string, updates: Partial<SessionInfo>) => void;
  
  // Safety actions
  setSafetyState: (state: SafetyState) => void;
  setSafetyArmed: (armed: boolean) => void;
  setSafetyLevel: (level: SafetyLevel) => void;
  addSafetyViolation: (violation: SafetyViolation) => void;
  clearSafetyViolations: () => void;

  // Telemetry actions
  setStreaming: (streaming: boolean) => void;
  addTelemetryData: (data: TelemetryData) => void;
  clearTelemetryHistory: () => void;
  setVehicleInfo: (info: Partial<AppStore['vehicleInfo']>) => void;

  // Utility actions
  reset: () => void;
}

const initialState = {
  connectionStatus: 'NO_INTERFACE_CONNECTED' as ConnectionStatus,
  connectedInterface: null,
  availableInterfaces: [],
  currentSession: null,
  sessions: [],

  safetyState: {
    armed: false,
    level: 'ReadOnly' as SafetyLevel,
    violations: [],
  },
  safetyArmed: false,
  safetyLevel: 'ReadOnly' as SafetyLevel,

  isStreaming: false,
  currentTelemetry: null,
  telemetryHistory: [],
  maxHistorySize: 1000,

  vehicleInfo: {},
};

export const useAppStore = create<AppStore>()(
  subscribeWithSelector((set, get) => ({
    ...initialState,

    setConnectionStatus: (status) => set({ connectionStatus: status }),

    setConnectedInterface: (interfaceInfo) => set({ connectedInterface: interfaceInfo }),

    setAvailableInterfaces: (interfaces) => set({ availableInterfaces: interfaces }),

    setCurrentSession: (session) => set({ currentSession: session }),

    addSession: (session) => set((state) => ({
      sessions: [...state.sessions, session],
    })),

    updateSession: (id, updates) => set((state) => ({
      sessions: state.sessions.map(s => s.id === id ? { ...s, ...updates } : s),
      currentSession: state.currentSession?.id === id 
        ? { ...state.currentSession, ...updates }
        : state.currentSession,
    })),

    setSafetyState: (state) => set({ 
      safetyState: state,
      safetyArmed: state.armed,
      safetyLevel: state.level,
    }),

    setSafetyArmed: (armed) => set((state) => ({
      safetyArmed: armed,
      safetyState: { ...state.safetyState, armed },
    })),

    setSafetyLevel: (level) => set((state) => ({
      safetyLevel: level,
      safetyState: { ...state.safetyState, level },
    })),

    addSafetyViolation: (violation) => set((state) => ({
      safetyState: {
        ...state.safetyState,
        violations: [...state.safetyState.violations, violation],
      },
    })),

    clearSafetyViolations: () => set((state) => ({
      safetyState: {
        ...state.safetyState,
        violations: [],
      },
    })),

    setStreaming: (streaming) => set({ isStreaming: streaming }),

    addTelemetryData: (data) => set((state) => {
      const newHistory = [data, ...state.telemetryHistory];
      if (newHistory.length > state.maxHistorySize) {
        newHistory.pop();
      }
      return {
        currentTelemetry: data,
        telemetryHistory: newHistory,
      };
    }),

    clearTelemetryHistory: () => set({
      telemetryHistory: [],
      currentTelemetry: null,
    }),

    setVehicleInfo: (info) => set((state) => ({
      vehicleInfo: { ...state.vehicleInfo, ...info },
    })),

    reset: () => set(initialState),
  }))
);

// Selectors for commonly used combinations
export const useConnectionState = () => {
  const connectionStatus = useAppStore((state) => state.connectionStatus);
  const connectedInterface = useAppStore((state) => state.connectedInterface);
  const currentSession = useAppStore((state) => state.currentSession);
  
  return {
    connectionStatus,
    connectedInterface,
    currentSession,
    isConnected: connectionStatus === 'CONNECTED',
    isDisconnected: connectionStatus === 'NO_INTERFACE_CONNECTED',
    canConnect: connectionStatus === 'NO_INTERFACE_CONNECTED' || connectionStatus === 'ERROR',
  };
};

export const useSafetyState = () => {
  const safetyState = useAppStore((state) => state.safetyState);
  const safetyArmed = useAppStore((state) => state.safetyArmed);
  const safetyLevel = useAppStore((state) => state.safetyLevel);
  
  return {
    safetyState,
    safetyArmed,
    safetyLevel,
    canFlash: safetyArmed && safetyLevel === 'Flash',
    canApplyLive: safetyArmed && (safetyLevel === 'LiveApply' || safetyLevel === 'Flash'),
    hasCriticalViolations: safetyState.violations.some(v => v.severity === 'Critical'),
  };
};

export const useTelemetryState = () => {
  const isStreaming = useAppStore((state) => state.isStreaming);
  const currentTelemetry = useAppStore((state) => state.currentTelemetry);
  const telemetryHistory = useAppStore((state) => state.telemetryHistory);
  
  return {
    isStreaming,
    currentTelemetry,
    telemetryHistory,
    hasData: currentTelemetry !== null,
  };
};
