/**
 * System routes
 * Handles system-level operations like operator mode
 */

import { FastifyInstance } from 'fastify';
import { operatorMode } from '../modules/operator-modes';

export async function systemRoutes(fastify: FastifyInstance) {
  // Get current operator mode
  fastify.get('/operator-mode', async (request, reply) => {
    try {
      const mode = operatorMode.getCurrentMode();
      const config = operatorMode.getModeConfig();
      
      return {
        mode,
        displayName: config.displayName,
        description: config.description,
        color: config.color,
        requirements: operatorMode.getRequirements(),
      };
    } catch (error) {
      fastify.log.error('Failed to get operator mode:', error);
      reply.code(500).send({ error: 'Failed to get operator mode' });
    }
  });
}
