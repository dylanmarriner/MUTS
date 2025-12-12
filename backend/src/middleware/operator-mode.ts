import { FastifyRequest, FastifyReply } from 'fastify';
import { OperatorModeService } from '../modules/operator-modes';

/**
 * Middleware to enforce operator mode restrictions
 * Blocks ECU writes in DEV mode
 */
export const enforceWriteProtection = async (request: FastifyRequest, reply: FastifyReply) => {
  // Only check for write operations
  if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(request.method)) {
    const operatorModeService = OperatorModeService.getInstance();
    const modeConfig = operatorModeService.getModeConfig();
    
    if (!modeConfig.allowsEcuWrites) {
      return reply.status(403).send({
        error: 'ECU writes not allowed in current mode',
        mode: modeConfig.displayName,
        message: 'Switch to WORKSHOP or LAB mode to enable ECU writes'
      });
    }
  }
};

/**
 * Middleware to require real hardware
 * Blocks operations that need real hardware in mock mode
 */
export const requireRealHardware = async (request: FastifyRequest, reply: FastifyReply) => {
  const operatorModeService = OperatorModeService.getInstance();
  const modeConfig = operatorModeService.getModeConfig();
  
  if (modeConfig.requiresRealHardware) {
    // Check if real interface is connected
    // This would be implemented based on the actual interface detection
    const hasRealInterface = request.headers['x-interface-connected'] === 'true';
    
    if (!hasRealInterface) {
      return reply.status(400).send({
        error: 'Real hardware required',
        mode: modeConfig.displayName,
        message: 'Connect a real interface to perform this operation'
      });
    }
  }
};

/**
 * Middleware to require confirmation for dangerous operations
 */
export const requireConfirmation = async (request: FastifyRequest, reply: FastifyReply) => {
  const operatorModeService = OperatorModeService.getInstance();
  const modeConfig = operatorModeService.getModeConfig();
  
  if (modeConfig.requiresConfirmation) {
    const confirmed = request.headers['x-operation-confirmed'] === 'true';
    
    if (!confirmed) {
      return reply.status(428).send({
        error: 'Confirmation required',
        message: 'Set X-Operation-Confirmed: true header to proceed'
      });
    }
  }
};
