/**
 * Unified Tuning Platform API Routes
 * Engine-scoped endpoints with SafetyOrchestrator wrapper
 */

import { FastifyInstance, FastifyRequest } from 'fastify'
import { SafetyOrchestrator } from './safety-orchestrator'
import { VersaEngine } from './engines/versa-engine'
import { CobbEngine } from './engines/cobb-engine'
import { MdsEngine } from './engines/mds-engine'
import { registerWebSocketRoutes } from './websockets'
import { 
  MapChange, 
  Changeset, 
  SafetyLevel, 
  ApplySession, 
  FlashJob,
  EngineAction 
} from './interfaces'

// Initialize safety orchestrator
const safetyOrchestrator = new SafetyOrchestrator({
  defaultLevel: 'SIMULATE',
  requireArming: true,
  autoRevertMinutes: 10,
  maxConcurrentSessions: 1,
  requireVerification: true,
  snapshotInterval: 1000
})

// Register engines
const versaEngine = new VersaEngine()
const cobbEngine = new CobbEngine()
const mdsEngine = new MdsEngine()

safetyOrchestrator.registerEngine(versaEngine)
safetyOrchestrator.registerEngine(cobbEngine)
safetyOrchestrator.registerEngine(mdsEngine)

// Helper to get engine by ID
function getEngine(engineId: string) {
  const engine = safetyOrchestrator.getEngine(engineId)
  if (!engine) {
    throw new Error(`Engine ${engineId} not found`)
  }
  return engine
}

// Helper to validate engine ID
async function validateEngine(request: FastifyRequest) {
  const { engine } = request.params as { engine: string }
  if (!['versa', 'cobb', 'mds'].includes(engine)) {
    throw new Error('Invalid engine ID')
  }
  return engine
}

// Export routes
export const tuningPlatformRoutes = async (fastify: FastifyInstance) => {
  // Register WebSocket routes first
  registerWebSocketRoutes(fastify)

  // Engine discovery
  fastify.get('/tuning/engines', async (request, reply) => {
    const engines = safetyOrchestrator.getEngines()
    return {
      engines: engines.map(e => ({
        id: e.engineId,
        name: e.name,
        version: e.version,
        capabilities: e.capabilities
      })),
      systemStatus: await safetyOrchestrator.getSystemStatus()
    }
  })

  fastify.get('/api/tuning/status', async (request, reply) => {
    return await safetyOrchestrator.getSystemStatus()
  })

  fastify.post('/api/tuning/safety-level', async (request, reply) => {
    const { level } = request.body as { level: SafetyLevel }
    try {
      safetyOrchestrator.setSafetyLevel(level)
      return { success: true, level }
    } catch (error) {
      reply.code(400)
      return { error: error.message }
    }
  })

  fastify.post('/api/tuning/arm', async (request, reply) => {
    const { verificationCode } = request.body as { verificationCode: string }
    const success = safetyOrchestrator.arm(verificationCode)
    if (success) {
      return { success: true, armed: true }
    } else {
      reply.code(400)
      return { error: 'Invalid verification code' }
    }
  })

  fastify.post('/api/tuning/disarm', async (request, reply) => {
    safetyOrchestrator.disarm()
    return { success: true, armed: false }
  })

  // Engine-scoped routes
  fastify.get('/api/tuning/:engine/profiles', async (request, reply) => {
    const engineId = await validateEngine(request)
    const engine = getEngine(engineId)
    
    try {
      // In real implementation, would fetch from database
      const profiles = [] // await prisma.tuningProfile.findMany({ where: { engineId } })
      return { profiles }
    } catch (error) {
      reply.code(500)
      return { error: error.message }
    }
  })

  fastify.get('/api/tuning/:engine/maps', async (request, reply) => {
    const engineId = await validateEngine(request)
    const { profileId } = request.query as { profileId?: string }
    const engine = getEngine(engineId)
    
    try {
      const maps = await engine.listMaps(profileId || '')
      return { maps }
    } catch (error) {
      reply.code(500)
      return { error: error.message }
    }
  })

  fastify.get('/api/tuning/:engine/maps/:mapId', async (request, reply) => {
    const engineId = await validateEngine(request)
    const { mapId } = request.params as { mapId: string }
    const engine = getEngine(engineId)
    
    try {
      const mapData = await engine.getMap(mapId)
      return mapData
    } catch (error) {
      reply.code(404)
      return { error: error.message }
    }
  })

  fastify.put('/api/tuning/:engine/maps/:mapId', async (request, reply) => {
    const engineId = await validateEngine(request)
    const { mapId } = request.params as { mapId: string }
    const payload = request.body as any
    const engine = getEngine(engineId)
    
    try {
      const success = await engine.updateMap(mapId, payload)
      return { success }
    } catch (error) {
      reply.code(400)
      return { error: error.message }
    }
  })

  fastify.post('/api/tuning/:engine/changesets', async (request, reply) => {
    const engineId = await validateEngine(request)
    const { profileId, changes, author, notes } = request.body as {
      profileId: string
      changes: MapChange[]
      author: string
      notes?: string
    }
    const engine = getEngine(engineId)
    
    try {
      const changeset = await engine.createChangeset(profileId, changes, author, notes)
      return changeset
    } catch (error) {
      reply.code(400)
      return { error: error.message }
    }
  })

  fastify.get('/api/tuning/:engine/changesets', async (request, reply) => {
    const engineId = await validateEngine(request)
    const { profileId } = request.query as { profileId?: string }
    const engine = getEngine(engineId)
    
    try {
      const changesets = await engine.listChangesets(profileId || '')
      return { changesets }
    } catch (error) {
      reply.code(500)
      return { error: error.message }
    }
  })

  fastify.get('/api/tuning/:engine/changesets/:changesetId', async (request, reply) => {
    const engineId = await validateEngine(request)
    const { changesetId } = request.params as { changesetId: string }
    const engine = getEngine(engineId)
    
    try {
      const changeset = await engine.getChangeset(changesetId)
      if (!changeset) {
        reply.code(404)
        return { error: 'Changeset not found' }
      }
      return changeset
    } catch (error) {
      reply.code(500)
      return { error: error.message }
    }
  })

  fastify.post('/api/tuning/:engine/validate', async (request, reply) => {
    const engineId = await validateEngine(request)
    const changeset = request.body as Changeset
    
    try {
      const result = await safetyOrchestrator.validateChanges(engineId, changeset)
      return result
    } catch (error) {
      reply.code(400)
      return { error: error.message }
    }
  })

  fastify.post('/api/tuning/:engine/simulate', async (request, reply) => {
    const engineId = await validateEngine(request)
    const changeset = request.body as Changeset
    const engine = getEngine(engineId)
    
    try {
      const result = await engine.simulate(changeset)
      return result
    } catch (error) {
      reply.code(400)
      return { error: error.message }
    }
  })

  fastify.post('/api/tuning/:engine/live/start', async (request, reply) => {
    const engineId = await validateEngine(request)
    const { vehicleSessionId, changesetId } = request.body as {
      vehicleSessionId: string
      changesetId?: string
    }
    
    try {
      const session = await safetyOrchestrator.createApplySession(
        engineId,
        vehicleSessionId,
        changesetId
      )
      return session
    } catch (error) {
      reply.code(400)
      return { error: error.message }
    }
  })

  fastify.post('/api/tuning/:engine/live/arm', async (request, reply) => {
    const engineId = await validateEngine(request)
    const { sessionId, applyToken } = request.body as {
      sessionId: string
      applyToken: string
    }
    
    try {
      const success = await safetyOrchestrator.armSession(sessionId, applyToken)
      if (success) {
        const session = safetyOrchestrator.getSession(sessionId)
        return session
      } else {
        reply.code(400)
        return { error: 'Failed to arm session' }
      }
    } catch (error) {
      reply.code(400)
      return { error: error.message }
    }
  })

  fastify.post('/api/tuning/:engine/live/apply', async (request, reply) => {
    const engineId = await validateEngine(request)
    const { sessionId, technicianId, jobId } = request.body as { 
      sessionId: string
      technicianId?: string
      jobId?: string
    }
    
    try {
      const result = await safetyOrchestrator.applyLive(sessionId, technicianId, jobId)
      return result
    } catch (error) {
      reply.code(400)
      return { error: error.message }
    }
  })

  fastify.post('/api/tuning/:engine/live/revert', async (request, reply) => {
    const engineId = await validateEngine(request)
    const { sessionId } = request.body as { sessionId: string }
    
    try {
      const result = await safetyOrchestrator.revertLive(sessionId)
      return result
    } catch (error) {
      reply.code(400)
      return { error: error.message }
    }
  })

  fastify.post('/api/tuning/:engine/flash/prepare', async (request, reply) => {
    const engineId = await validateEngine(request)
    const { profileId, changesetId } = request.body as {
      profileId: string
      changesetId?: string
    }
    const engine = getEngine(engineId)
    
    try {
      const job = await engine.prepareFlash(profileId, changesetId)
      return job
    } catch (error) {
      reply.code(400)
      return { error: error.message }
    }
  })

  fastify.post('/api/tuning/:engine/flash/execute', async (request, reply) => {
    const engineId = await validateEngine(request)
    const { jobId, technicianId, jobTrackingId } = request.body as { 
      jobId: string
      technicianId?: string
      jobTrackingId?: string
    }
    const engine = getEngine(engineId)
    
    // CRITICAL SAFETY CHECK: Check operator mode for flash permissions
    const { operatorMode } = await import('../operator-modes');
    const writeCheck = operatorMode.validateEcuWrite('flash');
    
    if (!writeCheck.allowed) {
      reply.code(403).send({ 
        error: 'Flash operations disabled',
        message: writeCheck.reason
      })
      return
    }
    
    // CRITICAL: Require technician attribution in non-DEV modes
    if (operatorMode.getCurrentMode() !== 'dev' && !technicianId) {
      reply.code(403).send({ 
        error: 'Technician attribution required for flash operations'
      })
      return
    }
    
    try {
      await engine.executeFlash(jobId)
      
      // Log the flash operation if job tracking is available
      if (jobTrackingId && technicianId) {
        const { getJobTrackingService } = await import('../job-tracking');
        const jobService = getJobTrackingService(fastify.prisma);
        await jobService.logFlash(
          jobTrackingId,
          technicianId,
          `Engine flash executed (job: ${jobId})`,
          {
            engineId,
            flashJobId: jobId,
          }
        );
      }
      
      return { success: true }
    } catch (error) {
      reply.code(400)
      return { error: error.message }
    }
  })

  fastify.post('/api/tuning/:engine/flash/abort', async (request, reply) => {
    const engineId = await validateEngine(request)
    const { jobId } = request.body as { jobId: string }
    const engine = getEngine(engineId)
    
    try {
      await engine.abortFlash(jobId)
      return { success: true }
    } catch (error) {
      reply.code(400)
      return { error: error.message }
    }
  })

  fastify.get('/api/tuning/:engine/status', async (request, reply) => {
    const engineId = await validateEngine(request)
    const engine = getEngine(engineId)
    
    try {
      const status = await engine.status()
      return status
    } catch (error) {
      reply.code(500)
      return { error: error.message }
    }
  })

  // MDS-specific action routes
  fastify.get('/api/tuning/mds/actions', async (request, reply) => {
    const engine = getEngine('mds')
    
    try {
      const actions = await engine.listActions()
      return { actions }
    } catch (error) {
      reply.code(500)
      return { error: error.message }
    }
  })

  fastify.post('/api/tuning/mds/actions/:actionId', async (request, reply) => {
    const { actionId } = request.params as { actionId: string }
    const parameters = request.body as Record<string, any>
    const engine = getEngine('mds')
    
    try {
      const result = await engine.executeAction(actionId, parameters)
      return result
    } catch (error) {
      reply.code(400)
      return { error: error.message }
    }
  })

  // Error handler
  fastify.setErrorHandler((error, request, reply) => {
    fastify.log.error(error)
    
    // Return explicit error codes as required
    if (error.message.includes('not connected')) {
      reply.code(503)
      return { error: 'NO_INTERFACE_CONNECTED' }
    }
    
    if (error.message.includes('vehicle')) {
      reply.code(503)
      return { error: 'NO_VEHICLE_RESPONSE' }
    }
    
    if (error.message.includes('not supported')) {
      reply.code(400)
      return { error: 'UNSUPPORTED_BY_ENGINE' }
    }
    
    if (error.message.includes('validation')) {
      reply.code(400)
      return { error: 'VALIDATION_FAILED' }
    }
    
    if (error.message.includes('checksum')) {
      reply.code(400)
      return { error: 'CHECKSUM_FAILED' }
    }
    
    reply.code(500)
    return { error: 'INTERNAL_ERROR' }
  })
}

// Export safety orchestrator for other modules
export { safetyOrchestrator }
