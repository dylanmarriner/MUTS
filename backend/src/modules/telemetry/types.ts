/**
 * Telemetry Module Types
 * Types for real-time data streaming and CAN processing
 */

export interface CANMessage {
  id: number;
  data: Buffer;
  timestamp: number;
  bus: number;
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

export interface CANSignal {
  name: string;
  bitStart: number;
  bitLength: number;
  factor: number;
  offset: number;
  unit: string;
  endian: 'big' | 'little';
}

export interface DBCDefinition {
  messages: Record<string, {
    id: number;
    signals: Record<string, CANSignal>;
  }>;
}

export interface StreamConfig {
  enabled: boolean;
  sampleRate: number; // Hz
  bufferSize: number;
  compressionEnabled: boolean;
}

export interface TelemetrySession {
  id: string;
  startTime: number;
  endTime?: number;
  dataPoints: TelemetryData[];
  config: StreamConfig;
}
