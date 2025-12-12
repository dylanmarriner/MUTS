/**
 * Job Tracking Service
 * Manages vehicle service jobs and event logging
 */

import { PrismaClient } from '@prisma/client';
import { z } from 'zod';

const CreateJobSchema = z.object({
  vehicleId: z.string().optional(),
  ecuId: z.string().optional(),
  technicianId: z.string().optional(),
  operatorMode: z.enum(['dev', 'workshop', 'lab']).optional(),
  notes: z.string().optional(),
  vehicleInfo: z.string().optional(),
  interfaceInfo: z.string().optional(),
});

const CreateJobEventSchema = z.object({
  jobId: z.string().optional(),
  technicianId: z.string().optional(),
  category: z.enum(['diagnostic', 'tuning', 'flash', 'safety', 'error']).optional(),
  description: z.string().optional(),
  payload: z.string().optional(),
});

export class JobTrackingService {
  private prisma: PrismaClient;
  private activeJobs: Map<string, any> = new Map();

  constructor(prisma: PrismaClient) {
    this.prisma = prisma;
  }

  /**
   * Create a new job
   */
  async createJob(data: z.infer<typeof CreateJobSchema>) {
    const validated = CreateJobSchema.parse(data);
    
    // Provide defaults for required fields
    const jobData = {
      vehicleId: validated.vehicleId || 'UNKNOWN',
      technicianId: validated.technicianId || 'UNKNOWN',
      operatorMode: validated.operatorMode || 'dev',
      ecuId: validated.ecuId,
      notes: validated.notes,
      vehicleInfo: validated.vehicleInfo,
      interfaceInfo: validated.interfaceInfo,
    };
    
    const job = await this.prisma.job.create({
      data: jobData,
      include: {
        technician: true,
        ecu: true,
      },
    });

    // Log job creation event
    await this.logEvent({
      jobId: job.id,
      technicianId: job.technicianId,
      category: 'diagnostic',
      description: `Job created for vehicle ${job.vehicleId}`,
      payload: JSON.stringify({
        operatorMode: job.operatorMode,
        ecuId: job.ecuId,
      }),
    });

    // Track active job
    this.activeJobs.set(job.vehicleId, job);

    return job;
  }

  /**
   * Get active job for vehicle
   */
  async getActiveJob(vehicleId: string) {
    // Check cache first
    if (this.activeJobs.has(vehicleId)) {
      return this.activeJobs.get(vehicleId);
    }

    // Query database
    const job = await this.prisma.job.findFirst({
      where: {
        vehicleId,
        status: 'open',
      },
      include: {
        technician: true,
        ecu: true,
        events: {
          orderBy: { timestamp: 'desc' },
          take: 10,
        },
      },
    });

    if (job) {
      this.activeJobs.set(vehicleId, job);
    }

    return job;
  }

  /**
   * Close a job
   */
  async closeJob(jobId: string, technicianId: string, notes?: string) {
    const job = await this.prisma.job.update({
      where: { id: jobId },
      data: {
        status: 'closed',
        endTime: new Date(),
        notes,
      },
    });

    // Log job closure event
    await this.logEvent({
      jobId,
      technicianId,
      category: 'diagnostic',
      description: 'Job closed',
      payload: JSON.stringify({ notes }),
    });

    // Remove from active jobs
    const activeJob = Array.from(this.activeJobs.entries())
      .find(([_, job]) => job.id === jobId);
    
    if (activeJob) {
      this.activeJobs.delete(activeJob[0]);
    }

    return job;
  }

  /**
   * Log an event to a job
   */
  async logEvent(data: z.infer<typeof CreateJobEventSchema>) {
    const validated = CreateJobEventSchema.parse(data);
    
    // Provide defaults for required fields
    const eventData = {
      jobId: validated.jobId || 'UNKNOWN',
      technicianId: validated.technicianId || 'UNKNOWN',
      category: validated.category || 'error',
      description: validated.description || 'Unknown event',
      payload: validated.payload || '{}',
    };
    
    const event = await this.prisma.jobEvent.create({
      data: eventData,
    });

    return event;
  }

  /**
   * Log diagnostic events
   */
  async logDiagnostic(jobId: string, technicianId: string, description: string, data?: any) {
    return this.logEvent({
      jobId,
      technicianId,
      category: 'diagnostic',
      description,
      payload: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * Log tuning events
   */
  async logTuning(jobId: string, technicianId: string, description: string, data?: any) {
    return this.logEvent({
      jobId,
      technicianId,
      category: 'tuning',
      description,
      payload: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * Log flash events
   */
  async logFlash(jobId: string, technicianId: string, description: string, data?: any) {
    return this.logEvent({
      jobId,
      technicianId,
      category: 'flash',
      description,
      payload: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * Log safety events
   */
  async logSafety(jobId: string, technicianId: string, description: string, data?: any) {
    return this.logEvent({
      jobId,
      technicianId,
      category: 'safety',
      description,
      payload: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * Log error events
   */
  async logError(jobId: string, technicianId: string, description: string, data?: any) {
    return this.logEvent({
      jobId,
      technicianId,
      category: 'error',
      description,
      payload: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * Get job events with pagination
   */
  async getJobEvents(jobId: string, page = 1, limit = 50) {
    const skip = (page - 1) * limit;

    const [events, total] = await Promise.all([
      this.prisma.jobEvent.findMany({
        where: { jobId },
        orderBy: { timestamp: 'desc' },
        skip,
        take: limit,
        include: {
          technician: {
            select: {
              id: true,
              name: true,
              role: true,
            },
          },
        },
      }),
      this.prisma.jobEvent.count({
        where: { jobId },
      }),
    ]);

    return {
      events,
      pagination: {
        page,
        limit,
        total,
        pages: Math.ceil(total / limit),
      },
    };
  }

  /**
   * Get jobs for a technician
   */
  async getTechnicianJobs(technicianId: string, status?: string) {
    return this.prisma.job.findMany({
      where: {
        technicianId,
        ...(status && { status }),
      },
      include: {
        ecu: {
          select: {
            id: true,
            vin: true,
            ecuType: true,
          },
        },
        _count: {
          select: {
            events: true,
          },
        },
      },
      orderBy: { startTime: 'desc' },
    });
  }

  /**
   * Export job data
   */
  async exportJob(jobId: string, format: 'json' | 'csv') {
    const job = await this.prisma.job.findUnique({
      where: { id: jobId },
      include: {
        technician: true,
        ecu: true,
        events: {
          orderBy: { timestamp: 'asc' },
          include: {
            technician: {
              select: {
                id: true,
                name: true,
                role: true,
              },
            },
          },
        },
      },
    });

    if (!job) {
      throw new Error('Job not found');
    }

    if (format === 'json') {
      return JSON.stringify(job, null, 2);
    }

    if (format === 'csv') {
      // CSV format for events
      const headers = ['Timestamp', 'Category', 'Technician', 'Description', 'Payload'];
      const rows = job.events.map(event => [
        event.timestamp.toISOString(),
        event.category,
        event.technician.name,
        event.description,
        event.payload || '',
      ]);

      return [headers, ...rows]
        .map(row => row.map(cell => `"${cell}"`).join(','))
        .join('\n');
    }

    throw new Error(`Unsupported export format: ${format}`);
  }
}

// Singleton instance
let jobTrackingService: JobTrackingService;

export function getJobTrackingService(prisma?: PrismaClient) {
  if (!jobTrackingService) {
    if (!prisma) {
      throw new Error('Prisma client required for first initialization');
    }
    jobTrackingService = new JobTrackingService(prisma);
  }
  return jobTrackingService;
}
