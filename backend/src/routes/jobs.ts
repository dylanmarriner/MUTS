/**
 * Job tracking routes
 */

import { FastifyInstance } from 'fastify';
import { z } from 'zod';
import { getJobTrackingService } from '../modules/job-tracking';

const createJobSchema = z.object({
  vehicleId: z.string(),
  ecuId: z.string().optional(),
  technicianId: z.string(),
  operatorMode: z.enum(['dev', 'workshop', 'lab']),
  notes: z.string().optional(),
  vehicleInfo: z.string().optional(),
  interfaceInfo: z.string().optional(),
});

const createEventSchema = z.object({
  category: z.enum(['diagnostic', 'tuning', 'flash', 'safety', 'error']),
  description: z.string(),
  payload: z.string().optional(),
});

export default async function jobRoutes(fastify: FastifyInstance) {
  const jobService = getJobTrackingService(fastify.prisma);

  // Get active jobs
  fastify.get('/active', async (request, reply) => {
    try {
      const jobs = await fastify.prisma.job.findMany({
        where: { status: 'open' },
        include: {
          technician: true,
          ecu: true,
          _count: {
            select: {
              events: true,
            },
          },
        },
        orderBy: { startTime: 'desc' },
      });
      
      return jobs;
    } catch (error) {
      fastify.log.error('Failed to get active jobs:', error);
      reply.code(500).send({ error: 'Failed to get active jobs' });
    }
  });

  // Get job by ID
  fastify.get('/:id', async (request, reply) => {
    try {
      const params = z.object({ id: z.string() }).parse(request.params);
      
      const job = await fastify.prisma.job.findUnique({
        where: { id: params.id },
        include: {
          technician: true,
          ecu: true,
          flashSessions: true,
        },
      });
      
      if (!job) {
        reply.code(404).send({ error: 'Job not found' });
        return;
      }
      
      return job;
    } catch (error) {
      fastify.log.error('Failed to get job:', error);
      reply.code(500).send({ error: 'Failed to get job' });
    }
  });

  // Create new job
  fastify.post('/', async (request, reply) => {
    try {
      const data = createJobSchema.parse(request.body);
      const job = await jobService.createJob(data);
      
      reply.code(201).send(job);
    } catch (error) {
      fastify.log.error('Failed to create job:', error);
      reply.code(500).send({ error: 'Failed to create job' });
    }
  });

  // Close job
  fastify.post('/:id/close', async (request, reply) => {
    try {
      const params = z.object({ id: z.string() }).parse(request.params);
      const body = z.object({
        technicianId: z.string(),
        notes: z.string().optional(),
      }).parse(request.body);
      
      const job = await jobService.closeJob(params.id, body.technicianId, body.notes);
      
      return job;
    } catch (error) {
      fastify.log.error('Failed to close job:', error);
      reply.code(500).send({ error: 'Failed to close job' });
    }
  });

  // Get job events
  fastify.get('/:id/events', async (request, reply) => {
    try {
      const params = z.object({ 
        id: z.string(),
        page: z.string().optional().transform(Number).default('1'),
        limit: z.string().optional().transform(Number).default('50'),
      }).parse(request.params);
      
      const result = await jobService.getJobEvents(params.id, params.page, params.limit);
      
      return result;
    } catch (error) {
      fastify.log.error('Failed to get job events:', error);
      reply.code(500).send({ error: 'Failed to get job events' });
    }
  });

  // Add event to job
  fastify.post('/:id/events', async (request, reply) => {
    try {
      const params = z.object({ id: z.string() }).parse(request.params);
      const body = createEventSchema.parse(request.body);
      
      // Get job to find technician
      const job = await fastify.prisma.job.findUnique({
        where: { id: params.id },
        select: { technicianId: true },
      });
      
      if (!job) {
        reply.code(404).send({ error: 'Job not found' });
        return;
      }
      
      const event = await jobService.logEvent({
        jobId: params.id,
        technicianId: job.technicianId,
        ...body,
      });
      
      reply.code(201).send(event);
    } catch (error) {
      fastify.log.error('Failed to create event:', error);
      reply.code(500).send({ error: 'Failed to create event' });
    }
  });

  // Get technician jobs
  fastify.get('/technician/:technicianId', async (request, reply) => {
    try {
      const params = z.object({ 
        technicianId: z.string(),
        status: z.string().optional(),
      }).parse(request.params);
      
      const jobs = await jobService.getTechnicianJobs(
        params.technicianId, 
        params.status
      );
      
      return jobs;
    } catch (error) {
      fastify.log.error('Failed to get technician jobs:', error);
      reply.code(500).send({ error: 'Failed to get technician jobs' });
    }
  });

  // Export job
  fastify.get('/:id/export', async (request, reply) => {
    try {
      const params = z.object({ 
        id: z.string(),
        format: z.enum(['json', 'csv']).default('json'),
      }).parse(request.query);
      
      const data = await jobService.exportJob(params.id, params.format);
      
      const filename = `job-${params.id}.${params.format}`;
      
      if (params.format === 'json') {
        reply.type('application/json');
      } else {
        reply.type('text/csv');
      }
      
      reply.header('Content-Disposition', `attachment; filename="${filename}"`);
      return data;
    } catch (error) {
      fastify.log.error('Failed to export job:', error);
      reply.code(500).send({ error: 'Failed to export job' });
    }
  });

  // Auto-create job when vehicle connects
  fastify.post('/auto-create', async (request, reply) => {
    try {
      const body = z.object({
        vehicleId: z.string(),
        ecuId: z.string().optional(),
        technicianId: z.string(),
        operatorMode: z.enum(['dev', 'workshop', 'lab']),
        interfaceInfo: z.string().optional(),
      }).parse(request.body);
      
      // Check if active job already exists
      const existingJob = await jobService.getActiveJob(body.vehicleId);
      if (existingJob) {
        return existingJob;
      }
      
      // Create new job
      const job = await jobService.createJob({
        ...body,
        notes: 'Auto-created on vehicle connection',
      });
      
      reply.code(201).send(job);
    } catch (error) {
      fastify.log.error('Failed to auto-create job:', error);
      reply.code(500).send({ error: 'Failed to auto-create job' });
    }
  });
}
