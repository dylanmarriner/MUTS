/**
 * Database Manager
 * Handles PostgreSQL database operations with Prisma
 */

import { Logger } from '../utils/logger';
import { PrismaClient } from '@prisma/client';

export interface VehicleInfo {
  vin: string;
  make: string;
  model: string;
  year: number;
  ecuType?: string;
  calibrationId?: string;
  metadata?: Record<string, any>;
}

export interface TelemetrySample {
  sessionId: string;
  timestamp: Date;
  signals: Record<string, number>;
  metadata?: Record<string, any>;
}

export interface DTCInfo {
  sessionId: string;
  dtcCode: string;
  description: string;
  status: 'active' | 'stored' | 'pending';
  timestamp: Date;
  freezeFrame?: Record<string, number>;
}

export interface TuningProfile {
  id: string;
  name: string;
  description: string;
  vehicleId: string;
  changeset: Record<string, any>;
  version: string;
  createdAt: Date;
  modifiedAt: Date;
}

export interface FlashJob {
  id: string;
  vehicleId: string;
  profileId?: string;
  status: 'pending' | 'preparing' | 'writing' | 'verifying' | 'complete' | 'failed' | 'aborted';
  progress: number;
  startTime: Date;
  endTime?: Date;
  checksum?: string;
  metadata?: Record<string, any>;
}

export class DatabaseManager {
  private logger: Logger;
  private prisma: PrismaClient;
  private initialized: boolean = false;

  constructor() {
    this.logger = new Logger('DatabaseManager');
    this.prisma = new PrismaClient({
      log: ['query', 'info', 'warn', 'error'],
    });
  }

  async initialize(): Promise<void> {
    if (this.initialized) {
      return;
    }

    try {
      // Test database connection
      await this.prisma.$connect();
      this.logger.info('Database connected successfully');

      // Run migrations if needed
      // Note: In production, migrations should be run separately
      this.initialized = true;
    } catch (error) {
      this.logger.error('Failed to initialize database:', error);
      throw error;
    }
  }

  async close(): Promise<void> {
    await this.prisma.$disconnect();
    this.logger.info('Database disconnected');
  }

  // Vehicle operations
  async createOrUpdateVehicle(vehicle: VehicleInfo): Promise<VehicleInfo> {
    try {
      const existing = await this.prisma.vehicle.findUnique({
        where: { vin: vehicle.vin },
      });

      if (existing) {
        const updated = await this.prisma.vehicle.update({
          where: { vin: vehicle.vin },
          data: {
            make: vehicle.make,
            model: vehicle.model,
            year: vehicle.year,
            ecuType: vehicle.ecuType,
            calibrationId: vehicle.calibrationId,
            metadata: vehicle.metadata || {},
            updatedAt: new Date(),
          },
        });
        return this.mapVehicle(updated);
      } else {
        const created = await this.prisma.vehicle.create({
          data: {
            vin: vehicle.vin,
            make: vehicle.make,
            model: vehicle.model,
            year: vehicle.year,
            ecuType: vehicle.ecuType,
            calibrationId: vehicle.calibrationId,
            metadata: vehicle.metadata || {},
          },
        });
        return this.mapVehicle(created);
      }
    } catch (error) {
      this.logger.error('Failed to create/update vehicle:', error);
      throw error;
    }
  }

  async getVehicle(vin: string): Promise<VehicleInfo | null> {
    try {
      const vehicle = await this.prisma.vehicle.findUnique({
        where: { vin },
      });
      return vehicle ? this.mapVehicle(vehicle) : null;
    } catch (error) {
      this.logger.error('Failed to get vehicle:', error);
      throw error;
    }
  }

  async getAllVehicles(): Promise<VehicleInfo[]> {
    try {
      const vehicles = await this.prisma.vehicle.findMany({
        orderBy: { updatedAt: 'desc' },
      });
      return vehicles.map(v => this.mapVehicle(v));
    } catch (error) {
      this.logger.error('Failed to get all vehicles:', error);
      throw error;
    }
  }

  // Session operations
  async createSession(session: {
    id: string;
    type: string;
    vehicleVin?: string;
    metadata?: Record<string, any>;
  }): Promise<void> {
    try {
      await this.prisma.session.create({
        data: {
          id: session.id,
          type: session.type,
          vehicleVin: session.vehicleVin,
          metadata: session.metadata || {},
          startTime: new Date(),
          status: 'active',
        },
      });
    } catch (error) {
      this.logger.error('Failed to create session:', error);
      throw error;
    }
  }

  async updateSession(
    id: string,
    updates: {
      status?: string;
      endTime?: Date;
      metadata?: Record<string, any>;
    }
  ): Promise<void> {
    try {
      await this.prisma.session.update({
        where: { id },
        data: updates,
      });
    } catch (error) {
      this.logger.error('Failed to update session:', error);
      throw error;
    }
  }

  async getSession(id: string): Promise<any> {
    try {
      return await this.prisma.session.findUnique({
        where: { id },
        include: {
          vehicle: true,
        },
      });
    } catch (error) {
      this.logger.error('Failed to get session:', error);
      throw error;
    }
  }

  // Telemetry operations
  async storeTelemetry(sample: TelemetrySample): Promise<void> {
    try {
      // Store signals as JSON
      await this.prisma.telemetry.create({
        data: {
          sessionId: sample.sessionId,
          timestamp: sample.timestamp,
          signals: sample.signals,
          metadata: sample.metadata || {},
        },
      });
    } catch (error) {
      this.logger.error('Failed to store telemetry:', error);
      // Don't throw - telemetry loss shouldn't stop the application
    }
  }

  async getTelemetry(
    sessionId: string,
    startTime?: Date,
    endTime?: Date,
    limit: number = 1000
  ): Promise<TelemetrySample[]> {
    try {
      const telemetry = await this.prisma.telemetry.findMany({
        where: {
          sessionId,
          timestamp: {
            gte: startTime,
            lte: endTime,
          },
        },
        orderBy: { timestamp: 'desc' },
        take: limit,
      });

      return telemetry.map(t => ({
        sessionId: t.sessionId,
        timestamp: t.timestamp,
        signals: t.signals as Record<string, number>,
        metadata: t.metadata as Record<string, any>,
      }));
    } catch (error) {
      this.logger.error('Failed to get telemetry:', error);
      throw error;
    }
  }

  async exportTelemetry(
    sessionId: string,
    format: 'csv' | 'json' = 'csv'
  ): Promise<Buffer> {
    try {
      const telemetry = await this.getTelemetry(sessionId);
      
      if (format === 'csv') {
        // Convert to CSV
        const headers = ['timestamp', ...Object.keys(telemetry[0]?.signals || {})];
        const rows = telemetry.map(t => [
          t.timestamp.toISOString(),
          ...Object.values(t.signals),
        ]);
        
        const csv = [headers, ...rows]
          .map(row => row.join(','))
          .join('\n');
        
        return Buffer.from(csv, 'utf-8');
      } else {
        // Return JSON
        return Buffer.from(JSON.stringify(telemetry, null, 2), 'utf-8');
      }
    } catch (error) {
      this.logger.error('Failed to export telemetry:', error);
      throw error;
    }
  }

  // DTC operations
  async storeDTC(dtc: DTCInfo): Promise<void> {
    try {
      await this.prisma.dTC.create({
        data: {
          sessionId: dtc.sessionId,
          code: dtc.dtcCode,
          description: dtc.description,
          status: dtc.status,
          timestamp: dtc.timestamp,
          freezeFrame: dtc.freezeFrame || {},
        },
      });
    } catch (error) {
      this.logger.error('Failed to store DTC:', error);
      throw error;
    }
  }

  async getDTCs(sessionId?: string): Promise<DTCInfo[]> {
    try {
      const dtcs = await this.prisma.dTC.findMany({
        where: {
          sessionId,
        },
        orderBy: { timestamp: 'desc' },
      });

      return dtcs.map(d => ({
        sessionId: d.sessionId,
        dtcCode: d.code,
        description: d.description,
        status: d.status as 'active' | 'stored' | 'pending',
        timestamp: d.timestamp,
        freezeFrame: d.freezeFrame as Record<string, number>,
      }));
    } catch (error) {
      this.logger.error('Failed to get DTCs:', error);
      throw error;
    }
  }

  async clearDTCs(sessionId: string): Promise<void> {
    try {
      await this.prisma.dTC.deleteMany({
        where: { sessionId },
      });
    } catch (error) {
      this.logger.error('Failed to clear DTCs:', error);
      throw error;
    }
  }

  // Tuning profile operations
  async createProfile(profile: Omit<TuningProfile, 'id' | 'createdAt' | 'modifiedAt'>): Promise<TuningProfile> {
    try {
      const created = await this.prisma.tuningProfile.create({
        data: {
          name: profile.name,
          description: profile.description,
          vehicleId: profile.vehicleId,
          changeset: profile.changeset,
          version: profile.version,
        },
      });

      return {
        id: created.id,
        name: created.name,
        description: created.description,
        vehicleId: created.vehicleId,
        changeset: created.changeset,
        version: created.version,
        createdAt: created.createdAt,
        modifiedAt: created.modifiedAt,
      };
    } catch (error) {
      this.logger.error('Failed to create tuning profile:', error);
      throw error;
    }
  }

  async getProfiles(vehicleId?: string): Promise<TuningProfile[]> {
    try {
      const profiles = await this.prisma.tuningProfile.findMany({
        where: {
          vehicleId,
        },
        orderBy: { modifiedAt: 'desc' },
      });

      return profiles.map(p => ({
        id: p.id,
        name: p.name,
        description: p.description,
        vehicleId: p.vehicleId,
        changeset: p.changeset,
        version: p.version,
        createdAt: p.createdAt,
        modifiedAt: p.modifiedAt,
      }));
    } catch (error) {
      this.logger.error('Failed to get tuning profiles:', error);
      throw error;
    }
  }

  // Flash job operations
  async createFlashJob(job: Omit<FlashJob, 'id' | 'startTime'>): Promise<FlashJob> {
    try {
      const created = await this.prisma.flashJob.create({
        data: {
          vehicleId: job.vehicleId,
          profileId: job.profileId,
          status: job.status,
          progress: job.progress,
          checksum: job.checksum,
          metadata: job.metadata || {},
        },
      });

      return {
        id: created.id,
        vehicleId: created.vehicleId,
        profileId: created.profileId,
        status: created.status as FlashJob['status'],
        progress: created.progress,
        startTime: created.startTime,
        endTime: created.endTime,
        checksum: created.checksum,
        metadata: created.metadata as Record<string, any>,
      };
    } catch (error) {
      this.logger.error('Failed to create flash job:', error);
      throw error;
    }
  }

  async updateFlashJob(
    id: string,
    updates: Partial<FlashJob>
  ): Promise<void> {
    try {
      await this.prisma.flashJob.update({
        where: { id },
        data: updates,
      });
    } catch (error) {
      this.logger.error('Failed to update flash job:', error);
      throw error;
    }
  }

  private mapVehicle(vehicle: any): VehicleInfo {
    return {
      vin: vehicle.vin,
      make: vehicle.make,
      model: vehicle.model,
      year: vehicle.year,
      ecuType: vehicle.ecuType,
      calibrationId: vehicle.calibrationId,
      metadata: vehicle.metadata as Record<string, any>,
    };
  }
}
