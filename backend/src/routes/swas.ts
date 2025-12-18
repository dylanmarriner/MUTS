import { FastifyPluginAsync } from 'fastify'
import { z } from 'zod'
import { prisma } from '../index'

const swasConfigSchema = z.object({
  ecuId: z.string(),
  enabled: z.boolean().optional(),
  reductionCurve: z.any(), // JSON array of angle vs reduction points
  activationAngle: z.number(),
  maxReduction: z.number(),
  responseTime: z.number() // milliseconds
})

const swasRoutes: FastifyPluginAsync = async (fastify) => {
  // Get all SWAS configurations
  fastify.get('/', async (request, reply) => {
    const query = z.object({
      ecuId: z.string().optional(),
      enabled: z.string().optional().transform(val => val === 'true')
    }).parse(request.query)
    
    const where: any = {}
    if (query.ecuId) where.ecuId = query.ecuId
    if (query.enabled !== undefined) where.enabled = query.enabled
    
    const configs = await prisma.sWASConfiguration.findMany({
      where,
      include: {
        ECU: {
          select: {
            id: true,
            vin: true,
            ecuType: true
          }
        }
      },
      orderBy: {
        createdAt: 'desc'
      }
    })
    
    return configs
  })

  // Get SWAS configuration by ID
  fastify.get('/:id', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    
    const config = await prisma.sWASConfiguration.findUnique({
      where: { id: params.id },
      include: {
        ECU: true
      }
    })

    if (!config) {
      reply.code(404).send({ error: 'SWAS configuration not found' })
      return
    }

    return config
  })

  // Create new SWAS configuration
  fastify.post('/', async (request, reply) => {
    const data = swasConfigSchema.parse(request.body)
    
    // Validate reduction curve format
    if (!Array.isArray(data.reductionCurve)) {
      reply.code(400).send({ error: 'Reduction curve must be an array' })
      return
    }
    
    const swasConfig = await prisma.sWASConfiguration.create({
      data: {
        enabled: data.enabled,
        reductionCurve: JSON.stringify(data.reductionCurve),
        activationAngle: data.activationAngle,
        maxReduction: data.maxReduction,
        responseTime: data.responseTime,
        ECU: { connect: { id: data.ecuId } }
      }
    })
    
    reply.code(201).send(swasConfig)
  })

  // Update SWAS configuration
  fastify.put('/:id', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const data = swasConfigSchema.partial().parse(request.body)
    
    try {
      const config = await prisma.sWASConfiguration.update({
        where: { id: params.id },
        data
      })
      return config
    } catch (error: any) {
      if (error.code === 'P2025') {
        reply.code(404).send({ error: 'SWAS configuration not found' })
        return
      }
      throw error
    }
  })

  // Delete SWAS configuration
  fastify.delete('/:id', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    
    try {
      await prisma.sWASConfiguration.delete({
        where: { id: params.id }
      })
      reply.code(204).send()
    } catch (error: any) {
      if (error.code === 'P2025') {
        reply.code(404).send({ error: 'SWAS configuration not found' })
        return
      }
      throw error
    }
  })

  // Get SWAS configuration by ECU
  fastify.get('/ecu/:ecuId', async (request, reply) => {
    const params = z.object({ ecuId: z.string() }).parse(request.params)
    
    const config = await prisma.sWASConfiguration.findFirst({
      where: { ecuId: params.ecuId },
      include: {
        ECU: true
      },
      orderBy: {
        createdAt: 'desc'
      }
    })
    
    if (!config) {
      reply.code(404).send({ error: 'No SWAS configuration found for this ECU' })
      return
    }
    
    return config
  })

  // Calculate torque reduction for given steering angle
  fastify.post('/:id/calculate-reduction', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const body = z.object({
      steeringAngle: z.number().min(-90).max(90), // degrees
      currentTorque: z.number()
    }).parse(request.body)
    
    try {
      const config = await prisma.sWASConfiguration.findUnique({
        where: { id: params.id }
      })
      
      if (!config) {
        reply.code(404).send({ error: 'SWAS configuration not found' })
        return
      }
      
      if (!config.enabled) {
        reply.send({
          reduction: 0,
          adjustedTorque: body.currentTorque,
          message: 'SWAS is disabled'
        })
        return
      }
      
      // Calculate reduction based on curve
      const absAngle = Math.abs(body.steeringAngle)
      let reductionPercentage = 0
      
      if (absAngle >= config.activationAngle) {
        // Find appropriate reduction from curve
        const curve = JSON.parse(config.reductionCurve) as Array<{angle: number, reduction: number}>
        
        for (let i = 0; i < curve.length - 1; i++) {
          if (absAngle >= curve[i].angle && absAngle <= curve[i + 1].angle) {
            // Linear interpolation
            const ratio = (absAngle - curve[i].angle) / (curve[i + 1].angle - curve[i].angle)
            reductionPercentage = curve[i].reduction + ratio * (curve[i + 1].reduction - curve[i].reduction)
            break
          }
        }
        
        // Cap at max reduction
        reductionPercentage = Math.min(reductionPercentage, config.maxReduction)
      }
      
      const reductionAmount = (body.currentTorque * reductionPercentage) / 100
      const adjustedTorque = body.currentTorque - reductionAmount
      
      reply.send({
        steeringAngle: body.steeringAngle,
        originalTorque: body.currentTorque,
        reductionPercentage,
        reductionAmount,
        adjustedTorque,
        activationAngle: config.activationAngle,
        responseTime: config.responseTime
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to calculate torque reduction' })
    }
  })

  // Get default reduction curve template
  fastify.get('/templates/reduction-curve', async (request, reply) => {
    const templates = {
      conservative: [
        { angle: 30, reduction: 0 },
        { angle: 45, reduction: 10 },
        { angle: 60, reduction: 25 },
        { angle: 90, reduction: 50 }
      ],
      aggressive: [
        { angle: 20, reduction: 0 },
        { angle: 35, reduction: 15 },
        { angle: 50, reduction: 35 },
        { angle: 90, reduction: 70 }
      ],
      linear: [
        { angle: 0, reduction: 0 },
        { angle: 90, reduction: 50 }
      ]
    }
    
    reply.send({
      templates,
      description: 'Angle in degrees vs reduction percentage',
      usage: 'Select a template or create custom curve points'
    })
  })

  // Enable/disable SWAS
  fastify.post('/:id/toggle', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const body = z.object({
      enabled: z.boolean()
    }).parse(request.body)
    
    try {
      const config = await prisma.sWASConfiguration.update({
        where: { id: params.id },
        data: { enabled: body.enabled }
      })
      
      reply.send({
        ...config,
        message: `SWAS ${body.enabled ? 'enabled' : 'disabled'}`
      })
    } catch (error: any) {
      if (error.code === 'P2025') {
        reply.code(404).send({ error: 'SWAS configuration not found' })
        return
      }
      throw error
    }
  })

  // Test SWAS response
  fastify.post('/:id/test-response', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    
    try {
      const config = await prisma.sWASConfiguration.findUnique({
        where: { id: params.id }
      })
      
      if (!config) {
        reply.code(404).send({ error: 'SWAS configuration not found' })
        return
      }
      
      // Simulate test sequence
      const testAngles = [0, 15, 30, 45, 60, 90]
      const baseTorque = 300
      
      const results = testAngles.map(angle => {
        const absAngle = Math.abs(angle)
        let reductionPercentage = 0
        
        if (absAngle >= config.activationAngle) {
          const curve = JSON.parse(config.reductionCurve) as Array<{angle: number, reduction: number}>
          
          for (let i = 0; i < curve.length - 1; i++) {
            if (absAngle >= curve[i].angle && absAngle <= curve[i + 1].angle) {
              const ratio = (absAngle - curve[i].angle) / (curve[i + 1].angle - curve[i].angle)
              reductionPercentage = curve[i].reduction + ratio * (curve[i + 1].reduction - curve[i].reduction)
              break
            }
          }
          
          reductionPercentage = Math.min(reductionPercentage, config.maxReduction)
        }
        
        const reductionAmount = (baseTorque * reductionPercentage) / 100
        const adjustedTorque = baseTorque - reductionAmount
        
        return {
          angle,
          reductionPercentage,
          adjustedTorque,
          responseTime: config.responseTime
        }
      })
      
      reply.send({
        testResults: results,
        config: {
          activationAngle: config.activationAngle,
          maxReduction: config.maxReduction,
          responseTime: config.responseTime
        },
        summary: {
          maxReductionApplied: Math.max(...results.map(r => r.reductionPercentage)),
          minTorqueOutput: Math.min(...results.map(r => r.adjustedTorque)),
          testCompleted: true
        }
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to test SWAS response' })
    }
  })
}

export default swasRoutes