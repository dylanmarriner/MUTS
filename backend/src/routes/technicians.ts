/**
 * Technician management routes
 */

import { FastifyInstance } from 'fastify';
import { z } from 'zod';

const createTechnicianSchema = z.object({
  name: z.string().min(1),
  role: z.string().optional(),
  certificationLevel: z.string().optional(),
});

const updateTechnicianSchema = z.object({
  name: z.string().min(1).optional(),
  role: z.enum(['tech', 'senior_tech', 'engineer']).optional(),
  certificationLevel: z.string().optional(),
  active: z.boolean().optional(),
});

export default async function technicianRoutes(fastify: FastifyInstance) {
  // Get all technicians
  fastify.get('/', async (request, reply) => {
    try {
      const technicians = await fastify.prisma.technician.findMany({
        orderBy: { name: 'asc' },
      });
      
      return technicians;
    } catch (error) {
      fastify.log.error('Failed to get technicians:', error);
      reply.code(500).send({ error: 'Failed to get technicians' });
    }
  });

  // Get active technicians
  fastify.get('/active', async (request, reply) => {
    try {
      const technicians = await fastify.prisma.technician.findMany({
        where: { active: true },
        orderBy: { name: 'asc' },
      });
      
      return technicians;
    } catch (error) {
      fastify.log.error('Failed to get active technicians:', error);
      reply.code(500).send({ error: 'Failed to get active technicians' });
    }
  });

  // Get technician by ID
  fastify.get('/:id', async (request, reply) => {
    try {
      const params = z.object({ id: z.string() }).parse(request.params);
      
      const technician = await fastify.prisma.technician.findUnique({
        where: { id: params.id },
        include: {
          jobs: {
            take: 10,
            orderBy: { startTime: 'desc' },
          },
          _count: {
            select: {
              jobs: true,
              jobEvents: true,
            },
          },
        },
      });
      
      if (!technician) {
        reply.code(404).send({ error: 'Technician not found' });
        return;
      }
      
      return technician;
    } catch (error) {
      fastify.log.error('Failed to get technician:', error);
      reply.code(500).send({ error: 'Failed to get technician' });
    }
  });

  // Create new technician
  fastify.post('/', async (request, reply) => {
    try {
      const data = createTechnicianSchema.parse(request.body);
      
      const technician = await fastify.prisma.technician.create({
        data: {
          name: data.name,
          role: data.role || 'technician',
        },
      });
      
      reply.code(201).send(technician);
    } catch (error) {
      fastify.log.error('Failed to create technician:', error);
      reply.code(500).send({ error: 'Failed to create technician' });
    }
  });

  // Update technician
  fastify.put('/:id', async (request, reply) => {
    try {
      const params = z.object({ id: z.string() }).parse(request.params);
      const data = updateTechnicianSchema.parse(request.body);
      
      const technician = await fastify.prisma.technician.update({
        where: { id: params.id },
        data,
      });
      
      return technician;
    } catch (error) {
      fastify.log.error('Failed to update technician:', error);
      reply.code(500).send({ error: 'Failed to update technician' });
    }
  });

  // Delete technician (soft delete by setting active=false)
  fastify.delete('/:id', async (request, reply) => {
    try {
      const params = z.object({ id: z.string() }).parse(request.params);
      
      // Check if technician has active jobs
      const activeJobs = await fastify.prisma.job.count({
        where: {
          technicianId: params.id,
          status: 'open',
        },
      });
      
      if (activeJobs > 0) {
        reply.code(400).send({ 
          error: 'Cannot delete technician with active jobs',
          activeJobs,
        });
        return;
      }
      
      await fastify.prisma.technician.update({
        where: { id: params.id },
        data: { active: false },
      });
      
      reply.code(204).send();
    } catch (error) {
      fastify.log.error('Failed to delete technician:', error);
      reply.code(500).send({ error: 'Failed to delete technician' });
    }
  });
}
