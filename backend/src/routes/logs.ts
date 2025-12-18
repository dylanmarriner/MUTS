import { FastifyPluginAsync } from 'fastify'
import { z } from 'zod'
import { prisma } from '../index'

const logSchema = z.object({
  ecuId: z.string(),
  fileName: z.string(),
  format: z.enum(['csv', 'log', 'bin']),
  startTime: z.string().transform(val => new Date(val)),
  endTime: z.string().transform(val => val ? new Date(val) : undefined).optional(),
  size: z.number()
})

const logRoutes: FastifyPluginAsync = async (fastify) => {
  // Get all logs
  fastify.get('/', async (request, reply) => {
    const query = z.object({
      ecuId: z.string().optional(),
      format: z.enum(['csv', 'log', 'bin']).optional(),
      processed: z.string().optional().transform(val => val === 'true'),
      limit: z.string().optional().transform(Number),
      offset: z.string().optional().transform(Number)
    }).parse(request.query)
    
    const where: any = {}
    if (query.ecuId) where.ecuId = query.ecuId
    if (query.format) where.format = query.format
    if (query.processed !== undefined) where.processed = query.processed
    
    const logs = await prisma.log.findMany({
      where,
      include: {
        ECU: {
          select: {
            id: true,
            vin: true,
            ecuType: true
          }
        },
        dynoResults: true,
        _count: {
          select: {
            torquePredictions: true
          }
        }
      },
      orderBy: {
        startTime: 'desc'
      },
      take: query.limit,
      skip: query.offset
    })
    
    return logs
  })

  // Create new log
  fastify.post('/', async (request, reply) => {
    const data = logSchema.parse(request.body)
    
    try {
      const log = await prisma.log.create({
        data: {
          fileName: data.fileName,
          format: data.format,
          startTime: data.startTime,
          endTime: data.endTime,
          size: data.size,
          processed: false,
          ECU: { connect: { id: data.ecuId } }
        },
        include: {
          ECU: true,
          dynoResults: true,
          torquePredictions: true
        }
      })
      reply.code(201).send(log)
    } catch (error: any) {
      if (error.code === 'P2002') {
        reply.code(409).send({ error: 'Log with this filename already exists' })
        return
      }
      throw error
    }
  })

  // Get log by ID
  fastify.get('/:id', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    
    const log = await prisma.log.findUnique({
      where: { id: params.id },
      include: {
        ECU: true,
        dynoResults: true,
        torquePredictions: {
          orderBy: {
            rpm: 'asc'
          }
        }
      }
    })

    if (!log) {
      reply.code(404).send({ error: 'Log not found' })
      return
    }

    return log
  })

  // Process log for analysis
  fastify.post('/:id/process', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    
    try {
      const log = await prisma.log.findUnique({
        where: { id: params.id },
        include: { ECU: true }
      })
      
      if (!log) {
        reply.code(404).send({ error: 'Log not found' })
        return
      }
      
      if (log.processed) {
        reply.code(400).send({ error: 'Log already processed' })
        return
      }
      
      // In real implementation, process the log file
      // For now, simulate processing
      
      // Create dyno results
      const dynoResult = await prisma.dynoResult.create({
        data: {
          power: JSON.stringify({
            peak: 250,
            atRpm: 5500,
            curve: [] // Would contain actual power curve data
          }),
          torque: JSON.stringify({
            peak: 300,
            atRpm: 4000,
            curve: [] // Would contain actual torque curve data
          }),
          peaks: JSON.stringify({
            maxPower: { value: 250, rpm: 5500 },
            maxTorque: { value: 300, rpm: 4000 }
          }),
          Log: { connect: { id: params.id } }
        }
      })
      
      // Create torque predictions for each gear
      const gears = [1, 2, 3, 4, 5, 6]
      for (const gear of gears) {
        for (let rpm = 1000; rpm <= 7000; rpm += 500) {
          const torquePrediction = await prisma.torquePrediction.create({
            data: {
              gear,
              rpm,
              torque: 250 + Math.random() * 100, // Simulated values
              confidence: 0.85 + Math.random() * 0.15,
              Log: { connect: { id: params.id } }
            }
          })
        }
      }
      
      // Mark log as processed
      const updatedLog = await prisma.log.update({
        where: { id: params.id },
        data: { processed: true }
      })
      
      reply.send({
        ...updatedLog,
        message: 'Log processed successfully',
        dynoResults: dynoResult,
        torquePredictionsCreated: gears.length * 13 // 13 RPM points per gear
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to process log' })
    }
  })

  // Get torque predictions for log
  fastify.get('/:id/torque-predictions', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const query = z.object({
      gear: z.string().optional().transform(Number),
      minRpm: z.string().optional().transform(Number),
      maxRpm: z.string().optional().transform(Number)
    }).parse(request.query)
    
    const where: any = { logId: params.id }
    if (query.gear) where.gear = query.gear
    if (query.minRpm || query.maxRpm) {
      where.rpm = {}
      if (query.minRpm) where.rpm.gte = query.minRpm
      if (query.maxRpm) where.rpm.lte = query.maxRpm
    }
    
    const predictions = await prisma.torquePrediction.findMany({
      where,
      orderBy: [
        { gear: 'asc' },
        { rpm: 'asc' }
      ]
    })
    
    return predictions
  })

  // Start data logging session
  fastify.post('/start-session', async (request, reply) => {
    const body = z.object({
      ecuId: z.string(),
      parameters: z.array(z.string()), // List of PIDs to log
      sampleRate: z.number().optional().default(10), // Hz
      bufferSize: z.number().optional().default(1000),
      compression: z.boolean().optional().default(true)
    }).parse(request.body)
    
    try {
      const ecu = await prisma.eCU.findUnique({
        where: { id: body.ecuId }
      })
      
      if (!ecu) {
        reply.code(404).send({ error: 'ECU not found' })
        return
      }
      
      // Create new log session
      const log = await prisma.log.create({
        data: {
          ecuId: body.ecuId,
          fileName: `log_${Date.now()}.${body.compression ? 'csv.gz' : 'csv'}`,
          format: 'csv',
          startTime: new Date(),
          size: 0,
          processed: false
        }
      })
      
      reply.send({
        success: true,
        sessionId: log.id,
        ecuType: ecu.ecuType,
        parameters: body.parameters,
        sampleRate: body.sampleRate,
        bufferSize: body.bufferSize,
        compression: body.compression,
        message: 'Logging session started'
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to start logging session' })
    }
  })

  // Stop data logging session
  fastify.post('/:id/stop-session', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    
    try {
      const log = await prisma.log.findUnique({
        where: { id: params.id }
      })
      
      if (!log) {
        reply.code(404).send({ error: 'Log session not found' })
        return
      }
      
      if (log.endTime) {
        reply.code(400).send({ error: 'Logging session already stopped' })
        return
      }
      
      // Update log with end time
      const updatedLog = await prisma.log.update({
        where: { id: params.id },
        data: {
          endTime: new Date(),
          size: Math.floor(Math.random() * 1000000) + 100000 // Simulated file size
        }
      })
      
      reply.send({
        success: true,
        sessionId: params.id,
        endTime: updatedLog.endTime,
        duration: updatedLog.endTime.getTime() - updatedLog.startTime.getTime(),
        size: updatedLog.size,
        message: 'Logging session stopped'
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to stop logging session' })
    }
  })

  // Stream live data
  fastify.get('/:id/stream', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const query = z.object({
      format: z.enum(['json', 'csv', 'binary']).optional().default('json'),
      realtime: z.boolean().optional().default(true)
    }).parse(request.query)
    
    try {
      const log = await prisma.log.findUnique({
        where: { id: params.id }
      })
      
      if (!log) {
        reply.code(404).send({ error: 'Log session not found' })
        return
      }
      
      if (log.endTime) {
        reply.code(400).send({ error: 'Cannot stream from completed session' })
        return
      }
      
      // Set up streaming response
      reply.raw.writeHead(200, {
        'Content-Type': query.format === 'json' ? 'application/json' : 'text/plain',
        'Transfer-Encoding': 'chunked',
        'Cache-Control': 'no-cache'
      })
      
      // Simulate streaming data
      const interval = setInterval(() => {
        const data = {
          timestamp: new Date().toISOString(),
          rpm: Math.floor(Math.random() * 3000) + 500,
          speed: Math.floor(Math.random() * 200),
          throttle: Math.random() * 100,
          afr: 14.7 + (Math.random() - 0.5),
          boost: Math.random() * 20
        }
        
        if (query.format === 'json') {
          reply.raw.write(JSON.stringify(data) + '\n')
        } else if (query.format === 'csv') {
          reply.raw.write(Object.values(data).join(',') + '\n')
        }
      }, 100)
      
      // Clean up on disconnect
      reply.raw.on('close', () => {
        clearInterval(interval)
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to stream data' })
    }
  })

  // Import log from file
  fastify.post('/import', async (request, reply) => {
    const body = z.object({
      ecuId: z.string(),
      fileName: z.string(),
      fileData: z.string(), // Base64 encoded file
      format: z.enum(['csv', 'log', 'bin']),
      delimiter: z.string().optional().default(','),
      headers: z.boolean().optional().default(true)
    }).parse(request.body)
    
    try {
      const ecu = await prisma.eCU.findUnique({
        where: { id: body.ecuId }
      })
      
      if (!ecu) {
        reply.code(404).send({ error: 'ECU not found' })
        return
      }
      
      // Decode file data
      const fileBuffer = Buffer.from(body.fileData, 'base64')
      
      // Create log entry
      const log = await prisma.log.create({
        data: {
          ecuId: body.ecuId,
          fileName: body.fileName,
          format: body.format,
          startTime: new Date(),
          size: fileBuffer.length,
          processed: false
        }
      })
      
      // Simulate parsing and importing
      const rowsParsed = Math.floor(fileBuffer.length / 50) // Estimate
      const columnsDetected = 8
      
      reply.send({
        success: true,
        logId: log.id,
        fileName: body.fileName,
        format: body.format,
        size: fileBuffer.length,
        rowsParsed,
        columnsDetected,
        message: 'Log imported successfully'
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to import log' })
    }
  })

  // Export log to file
  fastify.get('/:id/export', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const query = z.object({
      format: z.enum(['csv', 'json', 'xlsx', 'bin']).optional().default('csv'),
      includePredictions: z.boolean().optional().default(false),
      compression: z.boolean().optional().default(false)
    }).parse(request.query)
    
    try {
      const log = await prisma.log.findUnique({
        where: { id: params.id },
        include: {
          torquePredictions: query.includePredictions
        }
      })
      
      if (!log) {
        reply.code(404).send({ error: 'Log not found' })
        return
      }
      
      // Set appropriate headers
      const filename = `${log.fileName.split('.')[0]}_export.${query.format}${query.compression ? '.gz' : ''}`
      reply.header('Content-Disposition', `attachment; filename="${filename}"`)
      
      if (query.format === 'csv') {
        reply.type('text/csv')
        // Simulate CSV data
        reply.send('timestamp,rpm,speed,throttle,afr,boost\n' + 
                  '2023-01-01T10:00:00.000Z,2500,60,45,14.7,5.2\n')
      } else if (query.format === 'json') {
        reply.type('application/json')
        reply.send(JSON.stringify({
          metadata: {
            ecuId: log.ecuId,
            fileName: log.fileName,
            startTime: log.startTime,
            endTime: log.endTime
          },
          data: [
            { timestamp: '2023-01-01T10:00:00.000Z', rpm: 2500, speed: 60, throttle: 45, afr: 14.7, boost: 5.2 }
          ],
          predictions: query.includePredictions ? log.torquePredictions : undefined
        }, null, 2))
      } else {
        reply.type('application/octet-stream')
        reply.send(Buffer.from('binary log data'))
      }
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to export log' })
    }
  })

  // Analyze log patterns
  fastify.post('/:id/analyze-patterns', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const body = z.object({
      analysisType: z.enum(['performance', 'efficiency', 'driving_style', 'fault_detection']),
      timeWindow: z.number().optional(), // seconds
      sensitivity: z.number().min(0).max(1).optional().default(0.5)
    }).parse(request.body)
    
    try {
      const log = await prisma.log.findUnique({
        where: { id: params.id },
        include: { ECU: true }
      })
      
      if (!log) {
        reply.code(404).send({ error: 'Log not found' })
        return
      }
      
      // Simulate pattern analysis
      const analysis = {
        type: body.analysisType,
        patterns: [],
        insights: []
      }
      
      switch (body.analysisType) {
        case 'performance':
          analysis.patterns = [
            { pattern: 'Hard acceleration', frequency: 15, avgDuration: 3.2 },
            { pattern: 'High RPM usage', frequency: 8, avgRpm: 5500 }
          ]
          analysis.insights = ['Aggressive driving style detected', 'Frequent full throttle usage']
          break
        case 'efficiency':
          analysis.patterns = [
            { pattern: 'Coasting', frequency: 25, fuelSaved: 12.5 },
            { pattern: 'Steady speed', frequency: 40, avgEfficiency: 32.5 }
          ]
          analysis.insights = ['Good fuel efficiency habits', 'Optimal shift points']
          break
        case 'driving_style':
          analysis.patterns = [
            { pattern: 'Smooth acceleration', score: 8.5 },
            { pattern: 'Braking behavior', score: 7.2 }
          ]
          analysis.insights = ['Overall driving score: 7.8/10']
          break
        case 'fault_detection':
          analysis.patterns = [
            { anomaly: 'Misfire events', count: 3, severity: 'medium' },
            { anomaly: 'O2 sensor fluctuation', count: 12, severity: 'low' }
          ]
          analysis.insights = ['Minor issues detected, service recommended']
          break
      }
      
      reply.send({
        success: true,
        logId: params.id,
        analysis,
        sensitivity: body.sensitivity,
        processedAt: new Date().toISOString()
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to analyze patterns' })
    }
  })

  // Get log statistics
  fastify.get('/:id/statistics', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    
    try {
      const log = await prisma.log.findUnique({
        where: { id: params.id },
        include: {
          torquePredictions: true,
          dynoResults: true
        }
      })
      
      if (!log) {
        reply.code(404).send({ error: 'Log not found' })
        return
      }
      
      // Calculate statistics
      const duration = log.endTime ? 
        log.endTime.getTime() - log.startTime.getTime() : 
        Date.now() - log.startTime.getTime()
      
      const stats = {
        basic: {
          fileName: log.fileName,
          format: log.format,
          size: log.size,
          duration: duration,
          startTime: log.startTime,
          endTime: log.endTime
        },
        performance: {
          maxRpm: 6500,
          avgRpm: 2850,
          maxSpeed: 145,
          avgSpeed: 65,
          maxBoost: 18.5,
          avgBoost: 5.2
        },
        efficiency: {
          avgFuelConsumption: 8.5, // L/100km
          totalFuelUsed: 2.3, // L
          avgAfr: 14.7,
          co2Emissions: 5.4 // kg
        },
        analysis: {
          processed: log.processed,
          hasDynoResults: !!log.dynoResults,
          torquePredictions: log.torquePredictions.length,
          dataPoints: Math.floor(log.size / 64) // Estimate
        }
      }
      
      reply.send({
        success: true,
        logId: params.id,
        statistics: stats
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to get statistics' })
    }
  })

  // Get dyno results for log
  fastify.get('/:id/dyno', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    
    const dynoResult = await prisma.dynoResult.findUnique({
      where: { logId: params.id },
      include: {
        Log: {
          select: {
            id: true,
            fileName: true,
            startTime: true
          }
        }
      }
    })
    
    if (!dynoResult) {
      reply.code(404).send({ error: 'Dyno results not found for this log' })
      return
    }
    
    return dynoResult
  })

  // Delete log
  fastify.delete('/:id', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    
    try {
      await prisma.log.delete({
        where: { id: params.id }
      })
      reply.code(204).send()
    } catch (error: any) {
      if (error.code === 'P2025') {
        reply.code(404).send({ error: 'Log not found' })
        return
      }
      throw error
    }
  })

  // Get log statistics
  fastify.get('/stats/summary', async (request, reply) => {
    const stats = await prisma.log.groupBy({
      by: ['format', 'processed'],
      _count: {
        id: true
      },
      _sum: {
        size: true
      }
    })
    
    const totalLogs = await prisma.log.count()
    const processedLogs = await prisma.log.count({
      where: { processed: true }
    })
    
    return {
      total: totalLogs,
      processed: processedLogs,
      unprocessed: totalLogs - processedLogs,
      byFormat: stats,
      totalSize: stats.reduce((acc, curr) => acc + (curr._sum.size || 0), 0)
    }
  })

  // Upload log file
  fastify.post('/upload', async (request, reply) => {
    // In real implementation, handle file upload
    reply.send({
      message: 'Log upload endpoint',
      requirements: {
        formats: ['.csv', '.log', '.bin'],
        maxSize: '100MB',
        compression: ['zip', 'gzip']
      }
    })
  })
}

export default logRoutes