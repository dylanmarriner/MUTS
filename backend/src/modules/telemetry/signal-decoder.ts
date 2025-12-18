/**
 * Signal Decoder
 * Decodes CAN messages into telemetry data using DBC definitions
 */

import { EventEmitter } from 'events';
import { CANMessage, TelemetryData, CANSignal, DBCDefinition } from './types';

export class SignalDecoder extends EventEmitter {
  private dbc: DBCDefinition | null = null;

  async loadDBC(): Promise<void> {
    // Load DBC file with Mazda CAN definitions
    this.dbc = {
      messages: {
        'EngineData': {
          id: 0x7E0,
          signals: {
            engineRpm: { name: 'engineRpm', bitStart: 0, bitLength: 16, factor: 0.25, offset: 0, unit: 'RPM', endian: 'big' },
            boostPressure: { name: 'boostPressure', bitStart: 16, bitLength: 8, factor: 0.1, offset: -10, unit: 'PSI', endian: 'big' },
            afr: { name: 'afr', bitStart: 24, bitLength: 8, factor: 0.1, offset: 0, unit: 'AFR', endian: 'big' },
            timingAdvance: { name: 'timingAdvance', bitStart: 32, bitLength: 8, factor: 1, offset: -40, unit: 'degrees', endian: 'big' }
          }
        },
        'SensorData': {
          id: 0x7E1,
          signals: {
            fuelPressure: { name: 'fuelPressure', bitStart: 0, bitLength: 8, factor: 1, offset: 0, unit: 'PSI', endian: 'big' },
            iat: { name: 'iat', bitStart: 8, bitLength: 8, factor: 1, offset: -40, unit: '°C', endian: 'big' },
            ect: { name: 'ect', bitStart: 16, bitLength: 8, factor: 1, offset: -40, unit: '°C', endian: 'big' },
            vehicleSpeed: { name: 'vehicleSpeed', bitStart: 24, bitLength: 8, factor: 1, offset: 0, unit: 'km/h', endian: 'big' }
          }
        },
        'PedalData': {
          id: 0x7E2,
          signals: {
            throttlePosition: { name: 'throttlePosition', bitStart: 0, bitLength: 8, factor: 0.5, offset: 0, unit: '%', endian: 'big' },
            maf: { name: 'maf', bitStart: 8, bitLength: 16, factor: 0.01, offset: 0, unit: 'g/s', endian: 'big' },
            map: { name: 'map', bitStart: 24, bitLength: 8, factor: 0.1, offset: -10, unit: 'kPa', endian: 'big' },
            lambda: { name: 'lambda', bitStart: 32, bitLength: 8, factor: 0.01, offset: 0, unit: 'λ', endian: 'big' }
          }
        }
      }
    };
    
    this.emit('dbcLoaded');
  }

  decodeMessage(message: CANMessage): TelemetryData | null {
    if (!this.dbc) {
      return null;
    }

    // Find the message definition
    const messageDef = Object.values(this.dbc.messages).find(m => m.id === message.id);
    if (!messageDef) {
      return null;
    }

    // Decode signals
    const telemetry: Partial<TelemetryData> = {
      timestamp: message.timestamp
    };

    for (const [signalName, signal] of Object.entries(messageDef.signals)) {
      const value = this.decodeSignal(message.data, signal);
      (telemetry as any)[signalName] = value;
    }

    return telemetry as TelemetryData;
  }

  private decodeSignal(data: Buffer, signal: CANSignal): number {
    // Extract bits from buffer
    const startByte = Math.floor(signal.bitStart / 8);
    const endByte = Math.floor((signal.bitStart + signal.bitLength - 1) / 8);
    
    let value = 0;
    
    for (let i = startByte; i <= endByte && i < data.length; i++) {
      value <<= 8;
      value |= data[i];
    }
    
    // Apply bit mask
    const mask = (1 << signal.bitLength) - 1;
    const bitOffset = signal.bitStart % 8;
    value = (value >> bitOffset) & mask;
    
    // Apply factor and offset
    return (value * signal.factor) + signal.offset;
  }
}
