/**
 * Global Application Store
 * Manages connection, safety, and telemetry state across all tabs
 */

import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { shallow } from 'zustand/shallow';
import { OperatorMode, Technician } from '../types';

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

  // Operator state
  operatorMode: OperatorMode | null;
  technician: Technician | null;
  showStartup: boolean;
  setOperatorMode: (mode: OperatorMode | null) => void;
  setTechnician: (tech: Technician | null) => void;
  setShowStartup: (show: boolean) => void;

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

  // Operator state
  operatorMode: null as OperatorMode | null,
  technician: null as Technician | null,
  showStartup: true,
};

export const useAppStore = create<AppStore>()(
  subscribeWithSelector((set, get) => ({
    ...initialState,

    // Operator setters
    setOperatorMode: (mode) => set({ operatorMode: mode }),
    setTechnician: (tech) => set({ technician: tech }),
    setShowStartup: (show) => set({ showStartup: show }),

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
  return useAppStore(
    (state) => ({
      connectionStatus: state.connectionStatus,
      connectedInterface: state.connectedInterface,
      currentSession: state.currentSession,
      isConnected: state.connectionStatus === 'CONNECTED',
      isDisconnected: state.connectionStatus === 'NO_INTERFACE_CONNECTED',
      canConnect: state.connectionStatus === 'NO_INTERFACE_CONNECTED' || state.connectionStatus === 'ERROR',
    }),
    shallow
  );
};

export const useSafetyState = () => {
  return useAppStore(
    (state) => ({
      safetyState: state.safetyState,
      safetyArmed: state.safetyArmed,
      safetyLevel: state.safetyLevel,
      canFlash: state.safetyArmed && state.safetyLevel === 'Flash',
      canApplyLive: state.safetyArmed && (state.safetyLevel === 'LiveApply' || state.safetyLevel === 'Flash'),
      hasCriticalViolations: state.safetyState.violations.some(v => v.severity === 'Critical'),
    }),
    shallow
  );
};

export const useTelemetryState = () => {
  return useAppStore(
    (state) => ({
      isStreaming: state.isStreaming,
      currentTelemetry: state.currentTelemetry,
      telemetryHistory: state.telemetryHistory,
      hasData: state.currentTelemetry !== null,
    }),
    shallow
  );
};
