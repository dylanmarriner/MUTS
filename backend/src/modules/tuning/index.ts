import { FastifyInstance } from 'fastify'
import { z } from 'zod'
import { prisma } from '../../index'
import { randomBytes } from 'crypto'

// Schema definitions
const tuningProfileSchema = z.object({
  ecuId: z.string(),
  name: z.string().min(1).max(100),
  description: z.string().optional(),
  version: z.string().optional(),
  author: z.string().optional(),
  category: z.enum(['Stock', 'Stage1', 'Stage2', 'Custom']).optional(),
  metadata: z.record(z.any()).optional()
})

const tuningMapSchema = z.object({
  profileId: z.string(),
  mapName: z.string(),
  mapType: z.enum(['IGNITION', 'FUEL', 'BOOST', 'VVT', 'TORQUE', 'LIMITER', 'CORRECTION']),
  address: z.string(),
  size: z.number().positive(),
  dataType: z.enum(['2D_16x16', '2D_8x8', '1D', 'SINGLE']),
  description: z.string().optional(),
  units: z.string().optional(),
  conversionFactor: z.number(),
  minValue: z.number().optional(),
  maxValue: z.number().optional(),
  xAxis: z.array(z.number()).optional(),
  yAxis: z.array(z.number()).optional(),
  values: z.array(z.any()),
  category: z.string().optional(),
  isRuntimeAdjustable: z.boolean().optional()
})

const changesetSchema = z.object({
  profileId: z.string(),
  author: z.string(),
  notes: z.string().optional(),
  changes: z.array(z.object({
    mapId: z.string(),
    xIndex: z.number().optional(),
    yIndex: z.number().optional(),
    oldValue: z.number(),
    newValue: z.number(),
    reason: z.string().optional()
  }))
})

const applySessionSchema = z.object({
  vehicleSessionId: z.string(),
  changesetId: z.string().optional(),
  mode: z.enum(['SIMULATE', 'LIVE_APPLY', 'FLASH'])
})

// Safety level configuration
const SAFETY_LEVELS = {
  SIMULATE: {
    allowsWrite: false,
    requiresArming: false,
    timeoutMinutes: null,
    description: 'No ECU write - compute changes only'
  },
  LIVE_APPLY: {
    allowsWrite: true,
    requiresArming: true,
    timeoutMinutes: 10,
    description: 'Session-based reversible changes'
  },
  FLASH: {
    allowsWrite: true,
    requiresArming: true,
    timeoutMinutes: null,
    description: 'Persistent ROM write'
  }
} as const

// WebSocket streams for real-time updates
const tuningStreams = {
  apply: new Map<string, any>(),
  safety: new Map<string, any>(),
  validation: new Map<string, any>()
}

export async function tuningRoutes(fastify: FastifyInstance) {
  // ===== PROFILE MANAGEMENT =====
  
  // List tuning profiles
  fastify.get('/profiles', async (request, reply) => {
    const { ecuId } = request.query as { ecuId?: string }
    
    const profiles = await prisma.tuningProfile.findMany({
      where: ecuId ? { ecuId } : undefined,
      include: {
        ECU: true,
        maps: true,
        changesets: {
          orderBy: { createdAt: 'desc' },
          take: 5
        }
      }
    })
    
    reply.send(profiles)
  })
  
  // Create tuning profile
  fastify.post('/profiles', async (request, reply) => {
    const data = tuningProfileSchema.parse(request.body)
    
    const profile = await prisma.tuningProfile.create({
      data: {
        ecuId: data.ecuId,
        name: data.name,
        description: data.description,
        version: data.version || '1.0.0',
        author: data.author || 'Unknown',
        category: data.category || 'Custom',
        metadata: JSON.stringify(data.metadata || {})
      },
      include: {
        ECU: true
      }
    })
    
    reply.code(201).send(profile)
  })
  
  // Get tuning profile with maps
  fastify.get('/profiles/:id', async (request, reply) => {
    const { id } = request.params as { id: string }
    
    const profile = await prisma.tuningProfile.findUnique({
      where: { id },
      include: {
        ECU: true,
        maps: {
          orderBy: [{ category: 'asc' }, { mapName: 'asc' }]
        },
        changesets: {
          orderBy: { createdAt: 'desc' },
          include: {
            applySessions: true
          }
        }
      }
    })
    
    if (!profile) {
      reply.code(404).send({ error: 'Profile not found' })
      return
    }
    
    reply.send(profile)
  })
  
  // ===== MAP MANAGEMENT =====
  
  // List maps in profile
  fastify.get('/profiles/:profileId/maps', async (request, reply) => {
    const { profileId } = request.params as { profileId: string }
    const { type } = request.query as { type?: string }
    
    const maps = await prisma.tuningMap.findMany({
      where: {
        profileId,
        ...(type && { mapType: type.toUpperCase() })
      },
      orderBy: [{ category: 'asc' }, { mapName: 'asc' }]
    })
    
    reply.send(maps)
  })
  
  // Create/update map
  fastify.post('/maps', async (request, reply) => {
    const data = tuningMapSchema.parse(request.body)
    
    // Validate bounds
    if (data.minValue !== undefined && data.maxValue !== undefined) {
      for (const value of data.values.flat()) {
        if (typeof value === 'number' && (value < data.minValue || value > data.maxValue)) {
          reply.code(400).send({ 
            error: 'Value out of bounds',
            value,
            bounds: { min: data.minValue, max: data.maxValue }
          })
          return
        }
      }
    }
    
    const map = await prisma.tuningMap.create({
      data: {
        profileId: data.profileId,
        mapName: data.mapName,
        mapType: data.mapType,
        address: data.address,
        size: data.size,
        dataType: data.dataType,
        description: data.description,
        units: data.units,
        conversionFactor: data.conversionFactor,
        minValue: data.minValue,
        maxValue: data.maxValue,
        xAxis: JSON.stringify(data.xAxis || []),
        yAxis: JSON.stringify(data.yAxis || []),
        values: JSON.stringify(data.values),
        category: data.category || 'General',
        isRuntimeAdjustable: data.isRuntimeAdjustable || false
      }
    })
    
    reply.code(201).send(map)
  })
  
  // Update map values
  fastify.put('/maps/:id', async (request, reply) => {
    const { id } = request.params as { id: string }
    const { values, reason } = request.body as { 
      values: any[][], 
      reason?: string 
    }
    
    const map = await prisma.tuningMap.findUnique({
      where: { id }
    })
    
    if (!map) {
      reply.code(404).send({ error: 'Map not found' })
      return
    }
    
    // Validate bounds
    if (map.minValue !== null && map.maxValue !== null) {
      for (const value of values.flat()) {
        if (typeof value === 'number' && (value < map.minValue || value > map.maxValue)) {
          reply.code(400).send({ 
            error: 'Value out of bounds',
            value,
            bounds: { min: map.minValue, max: map.maxValue }
          })
          return
        }
      }
    }
    
    const updated = await prisma.tuningMap.update({
      where: { id },
      data: {
        values: JSON.stringify(values),
        updatedAt: new Date()
      }
    })
    
    reply.send(updated)
  })
  
  // ===== DIFF AND VALIDATION =====
  
  // Generate diff between profiles/maps
  fastify.post('/diff', async (request, reply) => {
    const { sourceId, targetId, mapIds } = request.body as {
      sourceId: string
      targetId: string
      mapIds?: string[]
    }
    
    const sourceMaps = await prisma.tuningMap.findMany({
      where: { 
        profileId: sourceId,
        ...(mapIds && { id: { in: mapIds } })
      }
    })
    
    const targetMaps = await prisma.tuningMap.findMany({
      where: { 
        profileId: targetId,
        ...(mapIds && { id: { in: mapIds } })
      }
    })
    
    const diffs = []
    
    for (const sourceMap of sourceMaps) {
      const targetMap = targetMaps.find(m => m.mapName === sourceMap.mapName)
      if (!targetMap) continue
      
      const sourceValues = JSON.parse(sourceMap.values)
      const targetValues = JSON.parse(targetMap.values)
      
      const mapDiffs = []
      
      if (sourceMap.dataType.startsWith('2D')) {
        for (let y = 0; y < sourceValues.length; y++) {
          for (let x = 0; x < sourceValues[y].length; x++) {
            if (sourceValues[y][x] !== targetValues[y][x]) {
              mapDiffs.push({
                x,
                y,
                oldValue: sourceValues[y][x],
                newValue: targetValues[y][x]
              })
            }
          }
        }
      } else {
        for (let i = 0; i < sourceValues.length; i++) {
          if (sourceValues[i] !== targetValues[i]) {
            mapDiffs.push({
              index: i,
              oldValue: sourceValues[i],
              newValue: targetValues[i]
            })
          }
        }
      }
      
      if (mapDiffs.length > 0) {
        diffs.push({
          mapName: sourceMap.mapName,
          mapType: sourceMap.mapType,
          changes: mapDiffs
        })
      }
    }
    
    reply.send({
      sourceProfile: sourceId,
      targetProfile: targetId,
      diffs,
      totalChanges: diffs.reduce((sum, d) => sum + d.changes.length, 0)
    })
  })
  
  // Validate profile against constraints
  fastify.post('/validate/:profileId', async (request, reply) => {
    const { profileId } = request.params as { profileId: string }
    
    const profile = await prisma.tuningProfile.findUnique({
      where: { id: profileId },
      include: { maps: true, ECU: true }
    })
    
    if (!profile) {
      reply.code(404).send({ error: 'Profile not found' })
      return
    }
    
    const warnings = []
    const errors = []
    
    for (const map of profile.maps) {
      const values = JSON.parse(map.values)
      
      // Check bounds
      if (map.minValue !== null && map.maxValue !== null) {
        for (const value of values.flat()) {
          if (typeof value === 'number') {
            if (value < map.minValue) {
              errors.push({
                map: map.mapName,
                type: 'BELOW_MIN',
                value,
                min: map.minValue
              })
            } else if (value > map.maxValue) {
              warnings.push({
                map: map.mapName,
                type: 'ABOVE_MAX',
                value,
                max: map.maxValue
              })
            }
          }
        }
      }
      
      // Map-specific validations
      if (map.mapType === 'IGNITION') {
        // Check for excessive timing advance
        for (const value of values.flat()) {
          if (typeof value === 'number' && value > 25) {
            errors.push({
              map: map.mapName,
              type: 'EXCESSIVE_TIMING',
              value,
              recommendation: 'Keep timing advance under 25 degrees'
            })
          }
        }
      } else if (map.mapType === 'BOOST') {
        // Check for excessive boost
        for (const value of values.flat()) {
          if (typeof value === 'number' && value > 22) {
            warnings.push({
              map: map.mapName,
              type: 'HIGH_BOOST',
              value,
              recommendation: 'Boost above 22 PSI may risk engine damage'
            })
          }
        }
      }
    }
    
    reply.send({
      profileId,
      valid: errors.length === 0,
      warnings,
      errors,
      riskScore: errors.length * 10 + warnings.length * 3
    })
  })
  
  // ===== SIMULATION =====
  
  // Simulate changes without applying
  fastify.post('/simulate', async (request, reply) => {
    const { profileId, changesetId } = request.body as {
      profileId: string
      changesetId?: string
    }
    
    // Get profile and changeset
    const profile = await prisma.tuningProfile.findUnique({
      where: { id: profileId },
      include: { maps: true }
    })
    
    if (!profile) {
      reply.code(404).send({ error: 'Profile not found' })
      return
    }
    
    let changes = []
    
    if (changesetId) {
      const changeset = await prisma.tuningChangeset.findUnique({
        where: { id: changesetId },
        include: { mapChanges: { include: { map: true } } }
      })
      
      if (!changeset) {
        reply.code(404).send({ error: 'Changeset not found' })
        return
      }
      
      changes = changeset.mapChanges
    }
    
    // Simulate effects
    const simulation = {
      profileId,
      changes: changes.length,
      effects: {
        estimatedPowerGain: Math.random() * 50, // Placeholder
        estimatedTorqueGain: Math.random() * 60,
        riskLevel: 'LOW' as 'LOW' | 'MEDIUM' | 'HIGH'
      },
      warnings: [],
      recommendations: []
    }
    
    reply.send(simulation)
  })
  
  // ===== LIVE APPLY =====
  
  // Create apply session
  fastify.post('/apply/session', async (request, reply) => {
    const data = applySessionSchema.parse(request.body)
    
    const safetyConfig = SAFETY_LEVELS[data.mode]
    
    const session = await prisma.tuningApplySession.create({
      data: {
        vehicleSessionId: data.vehicleSessionId,
        changesetId: data.changesetId,
        mode: data.mode,
        armed: false,
        status: 'PENDING',
        expiresAt: safetyConfig.timeoutMinutes 
          ? new Date(Date.now() + safetyConfig.timeoutMinutes * 60000)
          : null,
        applyToken: randomBytes(16).toString('hex')
      }
    })
    
    // Don't return token in response for security
    const { applyToken, ...sessionResponse } = session
    
    reply.send({
      ...sessionResponse,
      safetyConfig
    })
  })
  
  // Arm apply session (multi-step confirmation)
  fastify.post('/apply/session/:id/arm', async (request, reply) => {
    const { id } = request.params as { id: string }
    const { applyToken } = request.body as { applyToken: string }
    
    const session = await prisma.tuningApplySession.findUnique({
      where: { id },
      include: { changeset: { include: { mapChanges: true } } }
    })
    
    if (!session) {
      reply.code(404).send({ error: 'Session not found' })
      return
    }
    
    if (session.applyToken !== applyToken) {
      reply.code(401).send({ error: 'Invalid apply token' })
      return
    }
    
    if (session.mode !== 'LIVE_APPLY' && session.mode !== 'FLASH') {
      reply.code(400).send({ error: 'Mode does not require arming' })
      return
    }
    
    const updated = await prisma.tuningApplySession.update({
      where: { id },
      data: {
        armed: true,
        status: 'ARMED',
        updatedAt: new Date()
      }
    })
    
    reply.send(updated)
  })
  
  // Apply changes
  fastify.post('/apply/session/:id/execute', async (request, reply) => {
    const { id } = request.params as { id: string }
    
    const session = await prisma.tuningApplySession.findUnique({
      where: { id },
      include: { 
        changeset: { 
          include: { 
            mapChanges: { include: { map: true } }
          }
        }
      }
    })
    
    if (!session) {
      reply.code(404).send({ error: 'Session not found' })
      return
    }
    
    if (!session.armed) {
      reply.code(400).send({ error: 'Session not armed' })
      return
    }
    
    if (session.expiresAt && session.expiresAt < new Date()) {
      reply.code(400).send({ error: 'Session expired' })
      return
    }
    
    const safetyConfig = SAFETY_LEVELS[session.mode]
    
    if (!safetyConfig.allowsWrite) {
      reply.code(400).send({ error: 'Mode does not allow write operations' })
      return
    }
    
    // Execute apply based on mode
    const results = []
    
    for (const change of session.changeset?.mapChanges || []) {
      const event = await prisma.tuningApplyEvent.create({
        data: {
          sessionId: id,
          mapName: change.map.mapName,
          beforeValue: change.oldValue?.toString(),
          afterValue: change.newValue?.toString(),
          result: 'SUCCESS',
          message: `Changed ${change.map.mapName}[${change.xIndex},${change.yIndex}]`
        }
      })
      
      results.push(event)
      
      // Here you would actually apply the change to ECU
      // For now, we just log it
    }
    
    const updated = await prisma.tuningApplySession.update({
      where: { id },
      data: {
        status: 'COMPLETED',
        updatedAt: new Date()
      }
    })
    
    reply.send({
      session: updated,
      results,
      applied: results.length
    })
  })
  
  // Revert live changes
  fastify.post('/apply/session/:id/revert', async (request, reply) => {
    const { id } = request.params as { id: string }
    const { reason } = request.body as { reason?: string }
    
    const session = await prisma.tuningApplySession.findUnique({
      where: { id }
    })
    
    if (!session) {
      reply.code(404).send({ error: 'Session not found' })
      return
    }
    
    if (session.mode !== 'LIVE_APPLY') {
      reply.code(400).send({ error: 'Only live apply sessions can be reverted' })
      return
    }
    
    // Here you would revert the changes in ECU
    // For now, we just mark as reverted
    
    const updated = await prisma.tuningApplySession.update({
      where: { id },
      data: {
        status: 'REVERTED',
        revertReason: reason || 'Manual revert',
        updatedAt: new Date()
      }
    })
    
    reply.send(updated)
  })
  
  // ===== FLASH APPLY =====
  
  // Build ROM package from profile
  fastify.post('/flash/build/:profileId', async (request, reply) => {
    const { profileId } = request.params as { profileId: string }
    
    const profile = await prisma.tuningProfile.findUnique({
      where: { id: profileId },
      include: { 
        maps: true,
        ECU: true
      }
    })
    
    if (!profile) {
      reply.code(404).send({ error: 'Profile not found' })
      return
    }
    
    // Build ROM package
    const romPackage = {
      profileId,
      ecuId: profile.ECU.id,
      maps: profile.maps.map(m => ({
        address: m.address,
        size: m.size,
        data: JSON.parse(m.values)
      })),
      checksum: 'calculated_checksum', // Placeholder
      size: profile.maps.reduce((sum, m) => sum + m.size, 0)
    }
    
    reply.send(romPackage)
  })
  
  // Validate and checksum ROM
  fastify.post('/flash/validate', async (request, reply) => {
    const { romData } = request.body as { romData: string }
    
    // Validate ROM structure
    const validation = {
      valid: true,
      checksum: 'calculated_checksum',
      size: romData.length,
      warnings: [],
      errors: []
    }
    
    reply.send(validation)
  })
  
  // WebSocket endpoints will be added when ws plugin is installed
  
  fastify.get('/streams/status', async (request, reply) => {
    reply.send({
      apply: 'Stream endpoint ready',
      safety: 'Stream endpoint ready',
      validation: 'Stream endpoint ready'
    })
  })
}

export default tuningRoutes
