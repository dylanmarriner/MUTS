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
  try {
    const port = parseInt(process.env.PORT || '3000', 10)
    const host = process.env.HOST || '0.0.0.0'
    
    await fastify.listen({ port, host })
    fastify.log.info(`Server listening on ${host}:${port}`)
  } catch (err) {
    fastify.log.error(err)
    process.exit(1)
  }
}

start()