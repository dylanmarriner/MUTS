import { FastifyPluginAsync } from 'fastify'
import { z } from 'zod'
import { prisma } from '../index'
import { enforceWriteProtection, requireRealHardware, requireConfirmation } from '../middleware/operator-mode'

const diagnosticSessionSchema = z.object({
  ecuId: z.string(),
  status: z.enum(['running', 'completed', 'error']).optional()
})

const dtcSchema = z.object({
  code: z.string(),
  description: z.string(),
  severity: z.enum(['info', 'warning', 'error', 'critical']),
  status: z.enum(['active', 'stored', 'pending']),
  occurrenceCount: z.number().optional()
})

const liveDataSchema = z.object({
  pid: z.string(),
  name: z.string(),
  value: z.number(),
  unit: z.string().optional()
})

const diagnosticRoutes: FastifyPluginAsync = async (fastify) => {
  // Get all diagnostic sessions
  fastify.get('/', async (request, reply) => {
    const sessions = await prisma.diagnosticSession.findMany({
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
            dtcs: true,
            freezeFrames: true,
            liveData: true
          }
        }
      },
      orderBy: {
        startTime: 'desc'
      }
    })
    return sessions
  })

  // Get diagnostic session by ID
  fastify.get('/:id', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    
    const session = await prisma.diagnosticSession.findUnique({
      where: { id: params.id },
      include: {
        ECU: true,
        dtcs: true,
        freezeFrames: true,
        liveData: {
          orderBy: {
            timestamp: 'desc'
          }
        }
      }
    })

    if (!session) {
      reply.code(404).send({ error: 'Diagnostic session not found' })
      return
    }

    return session
  })

  // Create new diagnostic session
  fastify.post('/', { preHandler: [enforceWriteProtection] }, async (request, reply) => {
    const data = diagnosticSessionSchema.parse(request.body)
    const diagnosticSession = await prisma.diagnosticSession.create({
      data: {
        status: data.status || 'running',
        ECU: { connect: { id: data.ecuId } }
      },
      include: {
        ECU: true
      }
    })
    reply.code(201).send(diagnosticSession)
  })

  // Update diagnostic session
  fastify.put('/:id', { preHandler: [enforceWriteProtection] }, async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const data = diagnosticSessionSchema.partial().parse(request.body)
    
    try {
      const session = await prisma.diagnosticSession.update({
        where: { id: params.id },
        data: {
          ...data,
          endTime: data.status === 'completed' || data.status === 'error' ? new Date() : undefined
        }
      })
      return session
    } catch (error: any) {
      if (error.code === 'P2025') {
        reply.code(404).send({ error: 'Diagnostic session not found' })
        return
      }
      throw error
    }
  })

  // Delete diagnostic session
  fastify.delete('/:id', { preHandler: [enforceWriteProtection] }, async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    
    try {
      await prisma.diagnosticSession.delete({
        where: { id: params.id }
      })
      reply.code(204).send()
    } catch (error: any) {
      if (error.code === 'P2025') {
        reply.code(404).send({ error: 'Diagnostic session not found' })
        return
      }
      throw error
    }
  })

  // Add DTC to session
  fastify.post('/:id/dtc', { preHandler: [enforceWriteProtection] }, async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const data = dtcSchema.parse(request.body)
    
    try {
      const dtc = await prisma.dTC.create({
        data: {
          code: data.code,
          status: data.status,
          severity: data.severity,
          description: data.description,
          DiagnosticSession: { connect: { id: params.id } }
        }
      })
      reply.code(201).send(dtc)
    } catch (error: any) {
      if (error.code === 'P2003') {
        reply.code(404).send({ error: 'Diagnostic session not found' })
        return
      }
      throw error
    }
  })

  // Clear DTCs for session
  fastify.delete('/:id/dtc', { preHandler: [enforceWriteProtection] }, async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    
    try {
      await prisma.dTC.deleteMany({
        where: { diagnosticSessionId: params.id }
      })
      reply.code(204).send()
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to clear DTCs' })
    }
  })

  // Add live data
  fastify.post('/:id/live-data', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const data = liveDataSchema.parse(request.body)
    
    try {
      const liveData = await prisma.liveData.create({
        data: {
          name: data.name || data.pid,
          pid: data.pid,
          value: data.value,
          unit: data.unit,
          timestamp: new Date(),
          DiagnosticSession: { connect: { id: params.id } }
        }
      })
      reply.code(201).send(liveData)
    } catch (error: any) {
      if (error.code === 'P2003') {
        reply.code(404).send({ error: 'Diagnostic session not found' })
        return
      }
      throw error
    }
  })

  // Get live data for session
  fastify.get('/:id/live-data', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const query = z.object({
      pid: z.string().optional(),
      limit: z.string().optional().transform(Number)
    }).parse(request.query)
    
    const where: any = { diagnosticSessionId: params.id }
    if (query.pid) {
      where.pid = query.pid
    }
    
    const data = await prisma.liveData.findMany({
      where,
      orderBy: { timestamp: 'desc' },
      take: query.limit || 100
    })
    
    return data
  })

  // Diagnostic services - Read DTC Information
  fastify.post('/:id/read-dtc-info', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const body = z.object({
      dtcFormat: z.enum(['standard', 'enhanced', 'manufacturer']).optional().default('standard')
    }).parse(request.body)
    
    try {
      const session = await prisma.diagnosticSession.findUnique({
        where: { id: params.id },
        include: { ECU: true }
      })
      
      if (!session) {
        reply.code(404).send({ error: 'Diagnostic session not found' })
        return
      }
      
      // Simulate reading DTC information
      const dtcInfo = {
        format: body.dtcFormat,
        supportedTypes: ['powertrain', 'chassis', 'body', 'network'],
        storedCount: 5,
        activeCount: 2,
        pendingCount: 1,
        dtcs: [
          { code: 'P0300', description: 'Random/Multiple Cylinder Misfire Detected', status: 'active' },
          { code: 'P0420', description: 'Catalyst System Efficiency Below Threshold', status: 'stored' },
          { code: 'U0001', description: 'High Speed CAN Communication Bus', status: 'active' }
        ]
      }
      
      reply.send({
        success: true,
        service: 'ReadDTCInformation',
        ecuType: session.ECU.ecuType,
        ...dtcInfo
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to read DTC information' })
    }
  })

  // Diagnostic services - Clear Diagnostic Information
  fastify.post('/:id/clear-dtc', { preHandler: [enforceWriteProtection, requireRealHardware] }, async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const body = z.object({
      groupOfDTC: z.string().optional(), // Group identifier
      ecuAddresses: z.array(z.string()).optional() // Specific ECU addresses
    }).parse(request.body)
    
    try {
      const session = await prisma.diagnosticSession.findUnique({
        where: { id: params.id }
      })
      
      if (!session) {
        reply.code(404).send({ error: 'Diagnostic session not found' })
        return
      }
      
      // Clear DTCs from database
      await prisma.dTC.deleteMany({
        where: { diagnosticSessionId: params.id }
      })
      
      reply.send({
        success: true,
        service: 'ClearDiagnosticInformation',
        message: 'DTCs cleared successfully',
        groupOfDTC: body.groupOfDTC || 'all'
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to clear DTCs' })
    }
  })

  // Diagnostic services - Read Freeze Frame
  fastify.post('/:id/read-freeze-frame', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const body = z.object({
      dtcNumber: z.string().optional()
    }).parse(request.body)
    
    try {
      const session = await prisma.diagnosticSession.findUnique({
        where: { id: params.id },
        include: { freezeFrames: true }
      })
      
      if (!session) {
        reply.code(404).send({ error: 'Diagnostic session not found' })
        return
      }
      
      // Return freeze frames
      const freezeFrames = session.freezeFrames.map(ff => ({
        dtcCode: ff.dtcCode,
        timestamp: ff.timestamp,
        snapshot: ff.snapshot
      }))
      
      reply.send({
        success: true,
        service: 'ReadFreezeFrame',
        freezeFrames,
        count: freezeFrames.length
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to read freeze frame' })
    }
  })

  // Diagnostic services - Read Data By Identifier
  fastify.post('/:id/read-data-by-identifier', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const body = z.object({
      dataIdentifiers: z.array(z.string()) // Array of data IDs
    }).parse(request.body)
    
    try {
      const session = await prisma.diagnosticSession.findUnique({
        where: { id: params.id },
        include: { ECU: true }
      })
      
      if (!session) {
        reply.code(404).send({ error: 'Diagnostic session not found' })
        return
      }
      
      // Simulate reading data by identifier
      const data = body.dataIdentifiers.map(id => ({
        identifier: id,
        value: `0x${Math.floor(Math.random() * 0xFFFF).toString(16).padStart(4, '0')}`,
        description: `Data for ${id}`
      }))
      
      reply.send({
        success: true,
        service: 'ReadDataByIdentifier',
        ecuType: session.ECU.ecuType,
        data
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to read data by identifier' })
    }
  })

  // Diagnostic services - Write Data By Identifier
  fastify.post('/:id/write-data-by-identifier', { preHandler: [enforceWriteProtection, requireRealHardware] }, async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const body = z.object({
      dataIdentifier: z.string(),
      value: z.string(),
      confirmWrite: z.boolean().optional().default(true)
    }).parse(request.body)
    
    try {
      const session = await prisma.diagnosticSession.findUnique({
        where: { id: params.id }
      })
      
      if (!session) {
        reply.code(404).send({ error: 'Diagnostic session not found' })
        return
      }
      
      // Simulate writing data
      reply.send({
        success: true,
        service: 'WriteDataByIdentifier',
        dataIdentifier: body.dataIdentifier,
        valueWritten: body.value,
        confirmed: body.confirmWrite
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to write data by identifier' })
    }
  })

  // Diagnostic services - Routine Control
  fastify.post('/:id/routine-control', { preHandler: [enforceWriteProtection, requireRealHardware] }, async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const body = z.object({
      routineIdentifier: z.string(),
      controlOption: z.enum(['startRoutine', 'stopRoutine', 'requestRoutineResults']),
      parameters: z.array(z.string()).optional()
    }).parse(request.body)
    
    try {
      const session = await prisma.diagnosticSession.findUnique({
        where: { id: params.id }
      })
      
      if (!session) {
        reply.code(404).send({ error: 'Diagnostic session not found' })
        return
      }
      
      // Simulate routine control
      let result: any = {}
      
      switch (body.controlOption) {
        case 'startRoutine':
          result = {
            status: 'started',
            routineId: body.routineIdentifier,
            estimatedTime: 5000 // ms
          }
          break
        case 'stopRoutine':
          result = {
            status: 'stopped',
            routineId: body.routineIdentifier
          }
          break
        case 'requestRoutineResults':
          result = {
            status: 'completed',
            routineId: body.routineIdentifier,
            results: '0x12345678'
          }
          break
      }
      
      reply.send({
        success: true,
        service: 'RoutineControl',
        controlOption: body.controlOption,
        ...result
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to control routine' })
    }
  })

  // Diagnostic services - ECU Reset
  fastify.post('/:id/ecu-reset', { preHandler: [enforceWriteProtection, requireRealHardware, requireConfirmation] }, async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const body = z.object({
      resetType: z.enum(['hardReset', 'keyOffOnReset', 'softReset', 'rapidPowerDownReset', 'initiateDiagnosticSession'])
    }).parse(request.body)
    
    try {
      const session = await prisma.diagnosticSession.findUnique({
        where: { id: params.id },
        include: { ECU: true }
      })
      
      if (!session) {
        reply.code(404).send({ error: 'Diagnostic session not found' })
        return
      }
      
      // Update session status to reflect reset
      await prisma.diagnosticSession.update({
        where: { id: params.id },
        data: {
          status: 'running',
          endTime: null
        }
      })
      
      reply.send({
        success: true,
        service: 'ECUReset',
        resetType: body.resetType,
        ecuType: session.ECU.ecuType,
        message: 'ECU reset initiated successfully'
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to reset ECU' })
    }
  })

  // Diagnostic services - Request Download
  fastify.post('/:id/request-download', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const body = z.object({
      dataFormatIdentifier: z.string(),
      addressAndLengthFormatIdentifier: z.string(),
      memorySize: z.number(),
      memoryAddress: z.string().transform(val => parseInt(val, 16))
    }).parse(request.body)
    
    try {
      const session = await prisma.diagnosticSession.findUnique({
        where: { id: params.id }
      })
      
      if (!session) {
        reply.code(404).send({ error: 'Diagnostic session not found' })
        return
      }
      
      // Simulate request download
      reply.send({
        success: true,
        service: 'RequestDownload',
        dataFormatIdentifier: body.dataFormatIdentifier,
        memoryAddress: `0x${body.memoryAddress.toString(16)}`,
        memorySize: body.memorySize,
        blockSize: Math.min(body.memorySize, 4096), // Max block size
        message: 'Download request accepted'
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to request download' })
    }
  })

  // Diagnostic services - Transfer Data
  fastify.post('/:id/transfer-data', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const body = z.object({
      blockSequenceNumber: z.number(),
      data: z.string(), // Hex string
      transferRequestParameter: z.string().optional()
    }).parse(request.body)
    
    try {
      const session = await prisma.diagnosticSession.findUnique({
        where: { id: params.id }
      })
      
      if (!session) {
        reply.code(404).send({ error: 'Diagnostic session not found' })
        return
      }
      
      // Simulate data transfer
      const dataBuffer = Buffer.from(body.data, 'hex')
      
      reply.send({
        success: true,
        service: 'TransferData',
        blockSequenceNumber: body.blockSequenceNumber,
        bytesTransferred: dataBuffer.length,
        transferRequestParameter: body.transferRequestParameter || '00',
        message: 'Data transferred successfully'
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to transfer data' })
    }
  })

  // Diagnostic services - Request Transfer Exit
  fastify.post('/:id/request-transfer-exit', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    
    try {
      const session = await prisma.diagnosticSession.findUnique({
        where: { id: params.id }
      })
      
      if (!session) {
        reply.code(404).send({ error: 'Diagnostic session not found' })
        return
      }
      
      // Simulate transfer exit
      reply.send({
        success: true,
        service: 'RequestTransferExit',
        message: 'Transfer completed successfully'
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to exit transfer' })
    }
  })

  // Run full system scan
  fastify.post('/:id/full-scan', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    
    try {
      const session = await prisma.diagnosticSession.findUnique({
        where: { id: params.id },
        include: { ECU: true }
      })
      
      if (!session) {
        reply.code(404).send({ error: 'Diagnostic session not found' })
        return
      }
      
      // Update session status
      await prisma.diagnosticSession.update({
        where: { id: params.id },
        data: { status: 'running' }
      })
      
      // In a real implementation, this would trigger actual ECU communication
      // For now, we'll simulate the scan
      reply.send({ 
        message: 'Full system scan initiated',
        sessionId: params.id,
        status: 'running'
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to initiate scan' })
    }
  })
}

export default diagnosticRoutes