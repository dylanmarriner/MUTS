import { FastifyPluginAsync } from 'fastify'
import { z } from 'zod'
import { prisma } from '../index'

const torqueAdvisorySchema = z.object({
  ecuId: z.string(),
  gear: z.number().min(1).max(6),
  maxTorque: z.number(),
  recommendedMax: z.number(),
  reason: z.string().optional(),
  basedOnLogId: z.string().optional()
})

const torqueAdvisoryRoutes: FastifyPluginAsync = async (fastify) => {
  // Get all torque advisories
  fastify.get('/', async (request, reply) => {
    const query = z.object({
      ecuId: z.string().optional(),
      gear: z.string().optional().transform(Number),
      limit: z.string().optional().transform(Number)
    }).parse(request.query)
    
    const where: any = {}
    if (query.ecuId) where.ecuId = query.ecuId
    if (query.gear) where.gear = query.gear
    
    const advisories = await prisma.torqueAdvisory.findMany({
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
      },
      take: query.limit
    })
    
    return advisories
  })

  // Get torque advisory by ID
  fastify.get('/:id', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    
    const advisory = await prisma.torqueAdvisory.findUnique({
      where: { id: params.id },
      include: {
        ECU: true
      }
    })

    if (!advisory) {
      reply.code(404).send({ error: 'Torque advisory not found' })
      return
    }

    return advisory
  })

  // Create new torque advisory
  fastify.post('/', async (request, reply) => {
    const data = torqueAdvisorySchema.parse(request.body)
    
    const advisory = await prisma.torqueAdvisory.create({
      data: {
        gear: data.gear,
        maxTorque: data.maxTorque,
        recommendedMax: data.recommendedMax,
        reason: data.reason,
        basedOnLogId: data.basedOnLogId,
        ECU: { connect: { id: data.ecuId } }
      },
      include: {
        ECU: true
      }
    })
    
    reply.code(201).send(advisory)
  })

  // Update torque advisory
  fastify.put('/:id', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const data = torqueAdvisorySchema.partial().parse(request.body)
    
    try {
      const advisory = await prisma.torqueAdvisory.update({
        where: { id: params.id },
        data
      })
      return advisory
    } catch (error: any) {
      if (error.code === 'P2025') {
        reply.code(404).send({ error: 'Torque advisory not found' })
        return
      }
      throw error
    }
  })

  // Delete torque advisory
  fastify.delete('/:id', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    
    try {
      await prisma.torqueAdvisory.delete({
        where: { id: params.id }
      })
      reply.code(204).send()
    } catch (error: any) {
      if (error.code === 'P2025') {
        reply.code(404).send({ error: 'Torque advisory not found' })
        return
      }
      throw error
    }
  })

  // Get torque advisories by ECU
  fastify.get('/ecu/:ecuId', async (request, reply) => {
    const params = z.object({ ecuId: z.string() }).parse(request.params)
    
    const advisories = await prisma.torqueAdvisory.findMany({
      where: { ecuId: params.ecuId },
      include: {
        ECU: true
      },
      orderBy: [
        { gear: 'asc' },
        { createdAt: 'desc' }
      ]
    })
    
    // Group by gear for easier consumption
    const grouped = advisories.reduce((acc, advisory) => {
      if (!acc[advisory.gear]) {
        acc[advisory.gear] = []
      }
      acc[advisory.gear].push(advisory)
      return acc
    }, {} as Record<number, typeof advisories>)
    
    reply.send({
      ecuId: params.ecuId,
      advisoriesByGear: grouped,
      summary: {
        totalAdvisories: advisories.length,
        gearsCovered: Object.keys(grouped).length,
        lastUpdated: advisories.length > 0 ? advisories[0].createdAt : null
      }
    })
  })

  // Generate torque advisory from log
  fastify.post('/generate-from-log', async (request, reply) => {
    const body = z.object({
      logId: z.string(),
      ecuId: z.string(),
      safetyMargin: z.number().default(0.1) // 10% safety margin by default
    }).parse(request.body)
    
    try {
      // Get torque predictions from log
      const predictions = await prisma.torquePrediction.findMany({
        where: { logId: body.logId },
        orderBy: [
          { gear: 'asc' },
          { rpm: 'desc' } // Get peak torque first
        ]
      })
      
      if (predictions.length === 0) {
        reply.code(400).send({ error: 'No torque predictions found for this log' })
        return
      }
      
      // Group by gear and find max torque
      const maxTorqueByGear = predictions.reduce((acc: any, pred: any) => {
        if (!acc[pred.gear] || pred.torque > acc[pred.gear].torque) {
          acc[pred.gear] = pred
        }
        return acc
      }, {} as Record<number, any>)
      
      // Create advisories
      const advisories = []
      for (const [gear, prediction] of Object.entries(maxTorqueByGear) as [string, any][]) {
        const maxTorque = prediction.torque
        const recommendedMax = maxTorque * (1 - body.safetyMargin)
        
        const torqueAdvisory = await prisma.torqueAdvisory.create({
          data: {
            gear: parseInt(gear),
            maxTorque,
            recommendedMax,
            reason: `Generated from log analysis with ${body.safetyMargin * 100}% safety margin`,
            basedOnLogId: body.logId,
            ECU: { connect: { id: body.ecuId } }
          },
          include: {
            ECU: true
          }
        })
        
        advisories.push(torqueAdvisory)
      }
      
      reply.code(201).send({
        message: 'Torque advisories generated successfully',
        advisories,
        summary: {
          gearsProcessed: Object.keys(maxTorqueByGear).length,
          safetyMargin: body.safetyMargin,
          basedOnLogId: body.logId
        }
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to generate torque advisories' })
    }
  })

  // Get torque curve for specific gear
  fastify.get('/ecu/:ecuId/gear/:gear/curve', async (request, reply) => {
    const params = z.object({
      ecuId: z.string(),
      gear: z.string().transform(Number)
    }).parse(request.params)
    
    const query = z.object({
      logId: z.string().optional() // Get from specific log if provided
    }).parse(request.query)
    
    let predictions
    
    if (query.logId) {
      predictions = await prisma.torquePrediction.findMany({
        where: {
          logId: query.logId,
          gear: params.gear
        },
        orderBy: { rpm: 'asc' }
      })
    } else {
      // Get latest advisory and its source
      const advisory = await prisma.torqueAdvisory.findFirst({
        where: {
          ECU: { id: params.ecuId },
          gear: params.gear
        },
        orderBy: { createdAt: 'desc' },
        include: { ECU: true }
      })
      
      if (!advisory || !advisory.basedOnLogId) {
        reply.code(404).send({ error: 'No torque data found for this ECU and gear' })
        return
      }
      
      predictions = await prisma.torquePrediction.findMany({
        where: {
          logId: advisory.basedOnLogId,
          gear: params.gear
        },
        orderBy: { rpm: 'asc' }
      })
    }
    
    const curve = predictions.map(p => ({
      rpm: p.rpm,
      torque: p.torque,
      confidence: p.confidence
    }))
    
    reply.send({
      ecuId: params.ecuId,
      gear: params.gear,
      curve,
      metadata: {
        points: curve.length,
        maxTorque: Math.max(...curve.map(c => c.torque)),
        peakRpm: curve.reduce((max, curr) => curr.torque > max.torque ? curr : max, curve[0])?.rpm
      }
    })
  })

  // Compare advisories
  fastify.post('/compare', async (request, reply) => {
    const body = z.object({
      advisoryIds: z.array(z.string()).min(2).max(5)
    }).parse(request.body)
    
    const advisories = await prisma.torqueAdvisory.findMany({
      where: {
        id: { in: body.advisoryIds }
      },
      include: {
        ECU: true
      }
    })
    
    if (advisories.length !== body.advisoryIds.length) {
      reply.code(404).send({ error: 'One or more advisories not found' })
      return
    }
    
    // Group by ECU and gear
    const comparison = advisories.reduce((acc, advisory) => {
      const key = `${advisory.ECU.id}-${advisory.gear}`
      if (!acc[key]) {
        acc[key] = {
          ecuId: advisory.ECU.id,
          ecuType: advisory.ECU.ecuType,
          gear: advisory.gear,
          advisories: []
        }
      }
      acc[key].advisories.push({
        id: advisory.id,
        maxTorque: advisory.maxTorque,
        recommendedMax: advisory.recommendedMax,
        reason: advisory.reason,
        createdAt: advisory.createdAt
      })
      return acc
    }, {} as Record<string, any>)
    
    reply.send({
      comparison: Object.values(comparison),
      summary: {
        totalAdvisories: advisories.length,
        ecusCompared: [...new Set(advisories.map(a => a.ECU.id))].length,
        gearsCompared: [...new Set(advisories.map(a => a.gear))].length
      }
    })
  })
}

export default torqueAdvisoryRoutes