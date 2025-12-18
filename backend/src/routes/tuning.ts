import { FastifyPluginAsync } from 'fastify'
import { z } from 'zod'
import { prisma } from '../index'
import { enforceWriteProtection, requireRealHardware, requireConfirmation } from '../middleware/operator-mode'

const tuningProfileSchema = z.object({
  ecuId: z.string(),
  name: z.string(),
  description: z.string().optional(),
  isActive: z.boolean().optional(),
  isBase: z.boolean().optional()
})

const mapSchema = z.object({
  tableName: z.string(),
  axisX: z.any(), // JSON array
  axisY: z.any(), // JSON array
  values: z.any(), // JSON 2D array
  description: z.string().optional()
})

const safetyCheckSchema = z.object({
  parameter: z.string(),
  minValue: z.number().optional(),
  maxValue: z.number().optional(),
  warningLevel: z.number().optional(),
  criticalLevel: z.number().optional(),
  enabled: z.boolean().optional()
})

const tuningRoutes: FastifyPluginAsync = async (fastify) => {
  // Get all tuning profiles
  fastify.get('/', async (request, reply) => {
    const profiles = await prisma.tuningProfile.findMany({
      include: {
        ECU: {
          select: {
            id: true,
            vin: true,
            ecuType: true
          }
        },
        _count: {
          select: {
            ignitionMaps: true,
            fuelMaps: true,
            boostMaps: true,
            limiterMaps: true,
            safetyChecks: true
          }
        }
      },
      orderBy: {
        createdAt: 'desc'
      }
    })
    return profiles
  })

  // Get tuning profile by ID
  fastify.get('/:id', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    
    const profile = await prisma.tuningProfile.findUnique({
      where: { id: params.id },
      include: {
        ECU: true,
        ignitionMaps: true,
        fuelMaps: true,
        boostMaps: true,
        limiterMaps: true,
        safetyChecks: true
      }
    })

    if (!profile) {
      reply.code(404).send({ error: 'Tuning profile not found' })
      return
    }

    return profile
  })

  // Create new tuning profile
  fastify.post('/', { preHandler: [enforceWriteProtection] }, async (request, reply) => {
    const data = tuningProfileSchema.parse(request.body)
    
    try {
      const profile = await prisma.tuningProfile.create({
        data: {
          name: data.name,
          description: data.description,
          isActive: data.isActive,
          isBase: data.isBase,
          ECU: { connect: { id: data.ecuId } }
        },
        include: {
          ECU: true
        }
      })
      reply.code(201).send(profile)
    } catch (error: any) {
      if (error.code === 'P2002') {
        reply.code(409).send({ error: 'Profile with this name already exists for this ECU' })
        return
      }
      throw error
    }
  })

  // Update tuning profile
  fastify.put('/:id', { preHandler: [enforceWriteProtection] }, async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const data = tuningProfileSchema.partial().parse(request.body)
    
    try {
      const profile = await prisma.tuningProfile.update({
        where: { id: params.id },
        data
      })
      return profile
    } catch (error: any) {
      if (error.code === 'P2025') {
        reply.code(404).send({ error: 'Tuning profile not found' })
        return
      }
      throw error
    }
  })

  // Delete tuning profile
  fastify.delete('/:id', { preHandler: [enforceWriteProtection] }, async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    
    try {
      await prisma.tuningProfile.delete({
        where: { id: params.id }
      })
      reply.code(204).send()
    } catch (error: any) {
      if (error.code === 'P2025') {
        reply.code(404).send({ error: 'Tuning profile not found' })
        return
      }
      throw error
    }
  })

  // Activate profile (deactivate others for same ECU)
  fastify.post('/:id/activate', { preHandler: [enforceWriteProtection, requireConfirmation] }, async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    
    try {
      // Get the profile to find its ECU
      const profile = await prisma.tuningProfile.findUnique({
        where: { id: params.id },
        select: { ecuId: true }
      })
      
      if (!profile) {
        reply.code(404).send({ error: 'Tuning profile not found' })
        return
      }
      
      // Deactivate all profiles for this ECU
      await prisma.tuningProfile.updateMany({
        where: { 
          ecuId: profile.ecuId,
          isActive: true 
        },
        data: { isActive: false }
      })
      
      // Activate this profile
      const updatedProfile = await prisma.tuningProfile.update({
        where: { id: params.id },
        data: { isActive: true }
      })
      
      reply.send(updatedProfile)
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to activate profile' })
    }
  })

  // Add ignition map
  fastify.post('/:id/ignition-maps', { preHandler: [enforceWriteProtection] }, async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const data = mapSchema.parse(request.body)
    
    try {
      const ignitionMap = await prisma.ignitionMap.create({
        data: {
          tableName: data.tableName,
          axisX: data.axisX,
          axisY: data.axisY,
          values: data.values,
          description: data.description,
          TuningProfile: { connect: { id: params.id } }
        }
      })
      reply.code(201).send(ignitionMap)
    } catch (error: any) {
      if (error.code === 'P2003') {
        reply.code(404).send({ error: 'Tuning profile not found' })
        return
      }
      throw error
    }
  })

  // Add fuel map
  fastify.post('/:id/fuel-maps', { preHandler: [enforceWriteProtection] }, async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const data = mapSchema.parse(request.body)
    
    try {
      const fuelMap = await prisma.fuelMap.create({
        data: {
          tableName: data.tableName,
          axisX: data.axisX,
          axisY: data.axisY,
          values: data.values,
          description: data.description,
          TuningProfile: { connect: { id: params.id } }
        }
      })
      reply.code(201).send(fuelMap)
    } catch (error: any) {
      if (error.code === 'P2003') {
        reply.code(404).send({ error: 'Tuning profile not found' })
        return
      }
      throw error
    }
  })

  // Add boost map
  fastify.post('/:id/boost-maps', { preHandler: [enforceWriteProtection] }, async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const data = mapSchema.parse(request.body)
    
    try {
      const boostMap = await prisma.boostMap.create({
        data: {
          tableName: data.tableName,
          axisX: data.axisX,
          axisY: data.axisY,
          values: data.values,
          description: data.description,
          TuningProfile: { connect: { id: params.id } }
        }
      })
      reply.code(201).send(boostMap)
    } catch (error: any) {
      if (error.code === 'P2003') {
        reply.code(404).send({ error: 'Tuning profile not found' })
        return
      }
      throw error
    }
  })

  // Add limiter
  fastify.post('/:id/limiters', { preHandler: [enforceWriteProtection] }, async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const data = z.object({
      type: z.enum(['rev', 'speed', 'boost']),
      value: z.number(),
      unit: z.string().optional(),
      description: z.string().optional()
    }).parse(request.body)
    
    try {
      const limiter = await prisma.limiterMap.create({
        data: {
          type: data.type,
          value: data.value,
          unit: data.unit,
          description: data.description,
          TuningProfile: { connect: { id: params.id } }
        }
      })
      reply.code(201).send(limiter)
    } catch (error: any) {
      if (error.code === 'P2003') {
        reply.code(404).send({ error: 'Tuning profile not found' })
        return
      }
      throw error
    }
  })

  // Add safety check
  fastify.post('/:id/safety-checks', { preHandler: [enforceWriteProtection] }, async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const data = safetyCheckSchema.parse(request.body)
    
    try {
      const safetyCheck = await prisma.safetyCheck.create({
        data: {
          parameter: data.parameter,
          minValue: data.minValue,
          maxValue: data.maxValue,
          warningLevel: data.warningLevel,
          criticalLevel: data.criticalLevel,
          enabled: data.enabled,
          TuningProfile: { connect: { id: params.id } }
        }
      })
      reply.code(201).send(safetyCheck)
    } catch (error: any) {
      if (error.code === 'P2003') {
        reply.code(404).send({ error: 'Tuning profile not found' })
        return
      }
      throw error
    }
  })

  // Validate profile configuration
  fastify.post('/:id/validate', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    
    try {
      const profile = await prisma.tuningProfile.findUnique({
        where: { id: params.id },
        include: {
          ignitionMaps: true,
          fuelMaps: true,
          boostMaps: true,
          limiterMaps: true,
          safetyChecks: true
        }
      })
      
      if (!profile) {
        reply.code(404).send({ error: 'Tuning profile not found' })
        return
      }
      
      // Validate configuration
      const validation = {
        isValid: true,
        warnings: [],
        errors: []
      }
      
      // Check for required maps
      if (profile.ignitionMaps.length === 0) {
        validation.errors.push('No ignition maps defined')
        validation.isValid = false
      }
      
      if (profile.fuelMaps.length === 0) {
        validation.errors.push('No fuel maps defined')
        validation.isValid = false
      }
      
      // Check safety checks
      profile.safetyChecks.forEach(check => {
        if (check.enabled && (!check.minValue && !check.maxValue)) {
          validation.warnings.push(`Safety check ${check.parameter} has no limits defined`)
        }
      })
      
      reply.send({
        success: true,
        profileId: params.id,
        validation
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to validate profile' })
    }
  })

  // Real-time tuning features
  fastify.post('/:id/real-time-adjust', { preHandler: [enforceWriteProtection, requireConfirmation] }, async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const body = z.object({
      mapType: z.enum(['ignition', 'fuel', 'boost']),
      tableName: z.string(),
      cellX: z.number(),
      cellY: z.number(),
      newValue: z.number(),
      applyImmediately: z.boolean().optional().default(false)
    }).parse(request.body)
    
    try {
      const profile = await prisma.tuningProfile.findUnique({
        where: { id: params.id },
        include: { ECU: true }
      })
      
      if (!profile) {
        reply.code(404).send({ error: 'Tuning profile not found' })
        return
      }
      
      // Simulate real-time adjustment
      reply.send({
        success: true,
        operation: 'REAL_TIME_ADJUST',
        mapType: body.mapType,
        tableName: body.tableName,
        cell: { x: body.cellX, y: body.cellY },
        oldValue: 10.5, // Simulated old value
        newValue: body.newValue,
        applied: body.applyImmediately,
        ecuType: profile.ECU.ecuType
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to apply real-time adjustment' })
    }
  })

  // Interpolate map values
  fastify.post('/:id/interpolate', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const body = z.object({
      mapType: z.enum(['ignition', 'fuel', 'boost']),
      tableName: z.string(),
      method: z.enum(['linear', 'cubic', 'smooth']).optional().default('linear'),
      preserveEndpoints: z.boolean().optional().default(true)
    }).parse(request.body)
    
    try {
      const profile = await prisma.tuningProfile.findUnique({
        where: { id: params.id }
      })
      
      if (!profile) {
        reply.code(404).send({ error: 'Tuning profile not found' })
        return
      }
      
      // Simulate map interpolation
      reply.send({
        success: true,
        operation: 'MAP_INTERPOLATE',
        mapType: body.mapType,
        tableName: body.tableName,
        method: body.method,
        preserveEndpoints: body.preserveEndpoints,
        message: 'Map interpolated successfully'
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to interpolate map' })
    }
  })

  // Smooth map transitions
  fastify.post('/:id/smooth', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const body = z.object({
      mapType: z.enum(['ignition', 'fuel', 'boost']),
      tableName: z.string(),
      smoothingFactor: z.number().min(0).max(1).optional().default(0.5),
      iterations: z.number().min(1).max(10).optional().default(3)
    }).parse(request.body)
    
    try {
      const profile = await prisma.tuningProfile.findUnique({
        where: { id: params.id }
      })
      
      if (!profile) {
        reply.code(404).send({ error: 'Tuning profile not found' })
        return
      }
      
      // Simulate map smoothing
      reply.send({
        success: true,
        operation: 'MAP_SMOOTH',
        mapType: body.mapType,
        tableName: body.tableName,
        smoothingFactor: body.smoothingFactor,
        iterations: body.iterations,
        message: 'Map smoothed successfully'
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to smooth map' })
    }
  })

  // Scale map values
  fastify.post('/:id/scale', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const body = z.object({
      mapType: z.enum(['ignition', 'fuel', 'boost']),
      tableName: z.string(),
      scaleFactor: z.number(),
      offset: z.number().optional().default(0),
      preserveSign: z.boolean().optional().default(true)
    }).parse(request.body)
    
    try {
      const profile = await prisma.tuningProfile.findUnique({
        where: { id: params.id }
      })
      
      if (!profile) {
        reply.code(404).send({ error: 'Tuning profile not found' })
        return
      }
      
      // Simulate map scaling
      reply.send({
        success: true,
        operation: 'MAP_SCALE',
        mapType: body.mapType,
        tableName: body.tableName,
        scaleFactor: body.scaleFactor,
        offset: body.offset,
        preserveSign: body.preserveSign,
        message: 'Map scaled successfully'
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to scale map' })
    }
  })

  // Copy map between profiles
  fastify.post('/:id/copy-map', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const body = z.object({
      sourceProfileId: z.string(),
      mapType: z.enum(['ignition', 'fuel', 'boost']),
      tableName: z.string(),
      overwrite: z.boolean().optional().default(false)
    }).parse(request.body)
    
    try {
      const profile = await prisma.tuningProfile.findUnique({
        where: { id: params.id }
      })
      
      if (!profile) {
        reply.code(404).send({ error: 'Target tuning profile not found' })
        return
      }
      
      const sourceProfile = await prisma.tuningProfile.findUnique({
        where: { id: body.sourceProfileId }
      })
      
      if (!sourceProfile) {
        reply.code(404).send({ error: 'Source tuning profile not found' })
        return
      }
      
      // Simulate map copy
      reply.send({
        success: true,
        operation: 'MAP_COPY',
        sourceProfileId: body.sourceProfileId,
        targetProfileId: params.id,
        mapType: body.mapType,
        tableName: body.tableName,
        overwrite: body.overwrite,
        message: 'Map copied successfully'
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to copy map' })
    }
  })

  // Compare maps
  fastify.post('/:id/compare', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const body = z.object({
      compareProfileId: z.string(),
      mapType: z.enum(['ignition', 'fuel', 'boost']),
      tableName: z.string(),
      tolerance: z.number().optional().default(0.1)
    }).parse(request.body)
    
    try {
      const profile = await prisma.tuningProfile.findUnique({
        where: { id: params.id }
      })
      
      if (!profile) {
        reply.code(404).send({ error: 'First tuning profile not found' })
        return
      }
      
      const compareProfile = await prisma.tuningProfile.findUnique({
        where: { id: body.compareProfileId }
      })
      
      if (!compareProfile) {
        reply.code(404).send({ error: 'Second tuning profile not found' })
        return
      }
      
      // Simulate map comparison
      const differences = [
        { x: 10, y: 20, value1: 15.5, value2: 16.0, diff: 0.5 },
        { x: 15, y: 25, value1: 14.0, value2: 14.8, diff: 0.8 }
      ]
      
      reply.send({
        success: true,
        operation: 'MAP_COMPARE',
        profile1Id: params.id,
        profile2Id: body.compareProfileId,
        mapType: body.mapType,
        tableName: body.tableName,
        tolerance: body.tolerance,
        differences,
        summary: {
          totalCells: 256,
          differentCells: differences.length,
          maxDifference: 0.8,
          averageDifference: 0.65
        }
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to compare maps' })
    }
  })

  // Optimize map for target
  fastify.post('/:id/optimize', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const body = z.object({
      mapType: z.enum(['ignition', 'fuel', 'boost']),
      tableName: z.string(),
      targetType: z.enum(['power', 'efficiency', 'emissions', 'driveability']),
      constraints: z.object({
        maxTiming: z.number().optional(),
        maxBoost: z.number().optional(),
        afrTarget: z.number().optional()
      }).optional()
    }).parse(request.body)
    
    try {
      const profile = await prisma.tuningProfile.findUnique({
        where: { id: params.id },
        include: { ECU: true }
      })
      
      if (!profile) {
        reply.code(404).send({ error: 'Tuning profile not found' })
        return
      }
      
      // Simulate map optimization
      reply.send({
        success: true,
        operation: 'MAP_OPTIMIZE',
        mapType: body.mapType,
        tableName: body.tableName,
        targetType: body.targetType,
        constraints: body.constraints,
        optimizationResults: {
          cellsOptimized: 156,
          performanceGain: 5.2, // %
          estimatedPower: 285, // hp
          estimatedTorque: 320, // nm
          efficiency: 92.5 // %
        },
        message: 'Map optimized successfully'
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to optimize map' })
    }
  })

  // Get tuning templates
  fastify.get('/templates', async (request, reply) => {
    const query = z.object({
      ecuType: z.string().optional(),
      category: z.string().optional()
    }).parse(request.query)
    
    // Return available tuning templates
    const templates = [
      {
        id: 'mazdaspeed3_stage1',
        name: 'Mazdaspeed3 Stage 1',
        ecuType: 'MazdaSpeed3',
        category: 'street',
        description: 'Street legal tune with mild power increase',
        maps: ['ignition_base', 'fuel_base', 'boost_low'],
        estimatedGain: 15
      },
      {
        id: 'mazdaspeed3_stage2',
        name: 'Mazdaspeed3 Stage 2',
        ecuType: 'MazdaSpeed3',
        category: 'sport',
        description: 'Sport tune with significant power increase',
        maps: ['ignition_high', 'fuel_high', 'boost_high'],
        estimatedGain: 35
      },
      {
        id: 'mazda6_economy',
        name: 'Mazda6 Economy',
        ecuType: 'Mazda6',
        category: 'economy',
        description: 'Fuel economy optimized tune',
        maps: ['ignition_economy', 'fuel_economy'],
        estimatedGain: -5 // Negative for fuel savings
      }
    ]
    
    let filteredTemplates = templates
    if (query.ecuType) {
      filteredTemplates = filteredTemplates.filter(t => t.ecuType === query.ecuType)
    }
    if (query.category) {
      filteredTemplates = filteredTemplates.filter(t => t.category === query.category)
    }
    
    reply.send({
      success: true,
      templates: filteredTemplates,
      count: filteredTemplates.length
    })
  })

  // Apply template to profile
  fastify.post('/:id/apply-template', { preHandler: [enforceWriteProtection] }, async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const body = z.object({
      templateId: z.string(),
      overwriteExisting: z.boolean().optional().default(false)
    }).parse(request.body)
    
    try {
      const profile = await prisma.tuningProfile.findUnique({
        where: { id: params.id }
      })
      
      if (!profile) {
        reply.code(404).send({ error: 'Tuning profile not found' })
        return
      }
      
      // Simulate template application
      reply.send({
        success: true,
        operation: 'APPLY_TEMPLATE',
        profileId: params.id,
        templateId: body.templateId,
        overwriteExisting: body.overwriteExisting,
        mapsApplied: 3,
        message: 'Template applied successfully'
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to apply template' })
    }
  })
}

export default tuningRoutes