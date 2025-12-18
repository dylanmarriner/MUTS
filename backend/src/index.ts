import Fastify from 'fastify'
import cors from '@fastify/cors'
import { PrismaClient } from '@prisma/client'
import { z } from 'zod'

// Import route modules
import { tuningPlatformRoutes } from './modules/tuning-platform/index'
import securityRoutes from './routes/security'
import flashRoutes from './routes/flash'
import torqueAdvisoryRoutes from './routes/torque-advisory'
import swasRoutes from './routes/swas'
import agentRoutes from './routes/agents'
// import addRoutes from './routes/add' // Temporarily disabled - uses Express Router instead of Fastify
import { systemRoutes } from './routes/system'
import technicianRoutes from './routes/technicians'
import jobRoutes from './routes/jobs'

const fastify = Fastify({
  logger: true
})

// Initialize Prisma client
export const prisma = new PrismaClient({
  log: ['query', 'info', 'warn', 'error'],
})

// Register plugins
fastify.register(cors, {
  origin: true, // Configure for production
})

// Register WebSocket plugin for tuning platform
fastify.register(import('@fastify/websocket'))

// Register routes
fastify.register(tuningPlatformRoutes, { prefix: '/api' })
fastify.register(securityRoutes, { prefix: '/api/security' })
fastify.register(flashRoutes, { prefix: '/api/flash' })
fastify.register(torqueAdvisoryRoutes, { prefix: '/api/torque-advisory' })
fastify.register(swasRoutes, { prefix: '/api/swas' })
fastify.register(agentRoutes, { prefix: '/api/agents' })
// fastify.register(addRoutes, { prefix: '/api/add' }) // Temporarily disabled - uses Express Router instead of Fastify
fastify.register(systemRoutes, { prefix: '/api/system' })
fastify.register(technicianRoutes, { prefix: '/api/technicians' })
fastify.register(jobRoutes, { prefix: '/api/jobs' })

// Add prisma to fastify instance for route access
fastify.decorate('prisma', prisma)

// Health check endpoint
fastify.get('/health', async (request, reply) => {
  return { 
    status: 'ok', 
    timestamp: new Date().toISOString(),
    version: '1.0.0'
  }
})

// Centralized error handler
fastify.setErrorHandler((error, request, reply) => {
  fastify.log.error(error)
  
  // Handle validation errors
  if (error.validation) {
    reply.status(400).send({
      error: 'Validation Error',
      details: error.validation
    })
    return
  }
  
  // Handle Prisma errors
  if (error.code?.startsWith('P')) {
    reply.status(500).send({
      error: 'Database Error',
      message: 'An error occurred while processing your request'
    })
    return
  }
  
  // Default error response
  reply.status(500).send({
    error: 'Internal Server Error',
    message: process.env.NODE_ENV === 'development' ? error.message : 'Something went wrong'
  })
})

// Graceful shutdown
process.on('SIGINT', async () => {
  await fastify.close()
  await prisma.$disconnect()
  process.exit(0)
})

process.on('SIGTERM', async () => {
  await fastify.close()
  await prisma.$disconnect()
  process.exit(0)
})

const start = async () => {
  // #region agent log
  const fs = require('fs');
  const path = require('path');
  const DEBUG_LOG_PATH = path.resolve(__dirname, '../../.cursor/debug.log');
  function writeDebugLog(location: string, message: string, data: any, hypothesisId: string) {
    try {
      const logDir = path.dirname(DEBUG_LOG_PATH);
      if (!fs.existsSync(logDir)) {
        fs.mkdirSync(logDir, { recursive: true });
      }
      const logEntry = JSON.stringify({
        location,
        message,
        data,
        timestamp: Date.now(),
        sessionId: 'debug-session',
        runId: 'run1',
        hypothesisId
      }) + '\n';
      fs.appendFileSync(DEBUG_LOG_PATH, logEntry, 'utf-8');
    } catch (err) {
      // Ignore log write errors
    }
  }
  writeDebugLog('backend/index.ts:101', 'start function entry', { env: { PORT: process.env.PORT, HOST: process.env.HOST } }, 'E');
  // #endregion
  
  try {
    const port = parseInt(process.env.PORT || '3000', 10)
    const host = process.env.HOST || '0.0.0.0'
    
    // #region agent log
    writeDebugLog('backend/index.ts:107', 'before fastify.listen', { port, host }, 'E');
    // #endregion
    
    await fastify.listen({ port, host })
    
    // #region agent log
    writeDebugLog('backend/index.ts:110', 'fastify.listen success', { port, host }, 'E');
    // #endregion
    
    fastify.log.info(`Server listening on ${host}:${port}`)
  } catch (err: any) {
    // #region agent log
    writeDebugLog('backend/index.ts:115', 'start function error', { error: err.message, code: err.code, stack: err.stack }, 'E');
    // #endregion
    fastify.log.error(err)
    process.exit(1)
  }
}

start()