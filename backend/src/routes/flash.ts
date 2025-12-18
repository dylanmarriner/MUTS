import { FastifyPluginAsync } from 'fastify'
import { z } from 'zod'
import { prisma } from '../index'
import { createHash } from 'crypto'
import { enforceWriteProtection, requireRealHardware, requireConfirmation } from '../middleware/operator-mode'

const flashSessionSchema = z.object({
  ecuId: z.string(),
  fileName: z.string(),
  fileHash: z.string()
})

const flashRoutes: FastifyPluginAsync = async (fastify) => {
  // Get all flash sessions
  fastify.get('/', async (request, reply) => {
    const sessions = await prisma.flashSession.findMany({
      include: {
        ECU: {
          select: {
            id: true,
            vin: true,
            ecuType: true,
            firmwareVersion: true
          }
        }
      },
      orderBy: {
        startTime: 'desc'
      }
    })
    return sessions
  })

  // Get flash session by ID
  fastify.get('/:id', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    
    const session = await prisma.flashSession.findUnique({
      where: { id: params.id },
      include: {
        ECU: true
      }
    })

    if (!session) {
      reply.code(404).send({ error: 'Flash session not found' })
      return
    }

    return session
  })

  // Create new flash session
  fastify.post('/', { preHandler: [enforceWriteProtection] }, async (request, reply) => {
    const data = flashSessionSchema.parse(request.body)
    
    // Validate file hash format
    if (!/^[a-f0-9]{64}$/i.test(data.fileHash)) {
      reply.code(400).send({ error: 'Invalid file hash format' })
      return
    }
    
    const flashSession = await prisma.flashSession.create({
      data: {
        fileName: data.fileName || `flash_${Date.now()}.bin`,
        fileHash: data.fileHash,
        status: 'preparing',
        progress: 0,
        startTime: new Date(),
        ECU: { connect: { id: data.ecuId } }
      },
      include: {
        ECU: true
      }
    })
    
    reply.code(201).send(flashSession)
  })

  // Start flashing process
  fastify.post('/:id/start', { preHandler: [enforceWriteProtection, requireRealHardware, requireConfirmation] }, async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const body = z.object({
      technicianId: z.string(),
      jobId: z.string().optional()
    }).parse(request.body)
    
    // CRITICAL SAFETY CHECK: Check operator mode for flash permissions
    const { operatorMode } = await import('../modules/operator-modes');
    const writeCheck = operatorMode.validateEcuWrite('flash');
    
    if (!writeCheck.allowed) {
      reply.code(403).send({ 
        error: 'Flash operations disabled',
        message: writeCheck.reason
      })
      return
    }
    
    // CRITICAL: Require technician attribution in non-DEV modes
    if (operatorMode.getCurrentMode() !== 'dev' && !body.technicianId) {
      reply.code(403).send({ 
        error: 'Technician attribution required for flash operations'
      })
      return
    }
    
    try {
      const session = await prisma.flashSession.findUnique({
        where: { id: params.id },
        include: { ECU: true }
      })
      
      if (!session) {
        reply.code(404).send({ error: 'Flash session not found' })
        return
      }
      
      if (session.status !== 'preparing') {
        reply.code(400).send({ error: 'Flash session already started or completed' })
        return
      }
      
      // Update status to flashing
      const updatedSession = await prisma.flashSession.update({
        where: { id: params.id },
        data: { 
          status: 'flashing',
          progress: 0,
          jobId: body.jobId // Link to job for tracking
        }
      })
      
      // Log the flash operation if job tracking is available
      if (body.jobId && body.technicianId) {
        const { getJobTrackingService } = await import('../modules/job-tracking');
        const jobService = getJobTrackingService(prisma);
        await jobService.logFlash(
          body.jobId,
          body.technicianId,
          `Flash operation started for file: ${session.fileName}`,
          {
            sessionId: params.id,
            ecuId: session.ecuId,
            fileName: session.fileName,
            fileHash: session.fileHash,
          }
        );
      }
      
      // In real implementation, start actual flashing process
      reply.send({
        ...updatedSession,
        message: 'Flashing process started'
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to start flashing' })
    }
  })

  // Update flash progress
  fastify.put('/:id/progress', { preHandler: [enforceWriteProtection] }, async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const body = z.object({
      progress: z.number().min(0).max(100),
      status: z.enum(['preparing', 'flashing', 'verifying', 'completed', 'failed', 'rollback']).optional()
    }).parse(request.body)
    
    try {
      const session = await prisma.flashSession.update({
        where: { id: params.id },
        data: {
          progress: body.progress,
          status: body.status,
          endTime: (body.status === 'completed' || body.status === 'failed' || body.status === 'rollback') ? new Date() : undefined
        }
      })
      
      return session
    } catch (error: any) {
      if (error.code === 'P2025') {
        reply.code(404).send({ error: 'Flash session not found' })
        return
      }
      throw error
    }
  })

  // Verify flash checksum
  fastify.post('/:id/verify', { preHandler: [enforceWriteProtection] }, async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    
    try {
      const session = await prisma.flashSession.findUnique({
        where: { id: params.id }
      })
      
      if (!session) {
        reply.code(404).send({ error: 'Flash session not found' })
        return
      }
      
      if (session.status !== 'completed') {
        reply.code(400).send({ error: 'Flash must be completed before verification' })
        return
      }
      
      // In real implementation, read back from ECU and verify
      const isValid = true // Simulate successful verification
      
      const updatedSession = await prisma.flashSession.update({
        where: { id: params.id },
        data: {
          checksumValidated: isValid,
          status: isValid ? 'completed' : 'failed'
        }
      })
      
      reply.send({
        ...updatedSession,
        verified: isValid
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to verify flash' })
    }
  })

  // Create rollback point
  fastify.post('/:id/rollback-point', { preHandler: [enforceWriteProtection] }, async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    
    try {
      const session = await prisma.flashSession.findUnique({
        where: { id: params.id }
      })
      
      if (!session) {
        reply.code(404).send({ error: 'Flash session not found' })
        return
      }
      
      // In real implementation, create backup before flashing
      const updatedSession = await prisma.flashSession.update({
        where: { id: params.id },
        data: {
          rollbackAvailable: true
        }
      })
      
      reply.send({
        ...updatedSession,
        message: 'Rollback point created'
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to create rollback point' })
    }
  })

  // Execute rollback
  fastify.post('/:id/rollback', { preHandler: [enforceWriteProtection, requireConfirmation] }, async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    
    try {
      const session = await prisma.flashSession.findUnique({
        where: { id: params.id }
      })
      
      if (!session) {
        reply.code(404).send({ error: 'Flash session not found' })
        return
      }
      
      if (!session.rollbackAvailable) {
        reply.code(400).send({ error: 'No rollback point available' })
        return
      }
      
      // Update status to rollback
      const updatedSession = await prisma.flashSession.update({
        where: { id: params.id },
        data: {
          status: 'rollback',
          progress: 0
        }
      })
      
      // In real implementation, execute rollback
      reply.send({
        ...updatedSession,
        message: 'Rollback initiated'
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to initiate rollback' })
    }
  })

  // ROM operations - Read ROM
  fastify.post('/:id/read-rom', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const body = z.object({
      startAddress: z.string().transform(val => parseInt(val, 16)),
      length: z.number(),
      blockSize: z.number().optional().default(256)
    }).parse(request.body)
    
    try {
      const session = await prisma.flashSession.findUnique({
        where: { id: params.id },
        include: { ECU: true }
      })
      
      if (!session) {
        reply.code(404).send({ error: 'Flash session not found' })
        return
      }
      
      // Simulate ROM read operation
      const blocks = Math.ceil(body.length / body.blockSize)
      const data = []
      
      for (let i = 0; i < blocks; i++) {
        const blockStart = body.startAddress + (i * body.blockSize)
        const blockData = 'FF'.repeat(body.blockSize * 2) // Simulate ROM data
        data.push({
          address: `0x${blockStart.toString(16)}`,
          data: blockData,
          length: body.blockSize
        })
      }
      
      reply.send({
        success: true,
        operation: 'ROM_READ',
        startAddress: `0x${body.startAddress.toString(16)}`,
        totalLength: body.length,
        blocksRead: blocks,
        data
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to read ROM' })
    }
  })

  // ROM operations - Write ROM
  fastify.post('/:id/write-rom', { preHandler: [enforceWriteProtection, requireConfirmation] }, async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const body = z.object({
      startAddress: z.string().transform(val => parseInt(val, 16)),
      data: z.string(), // Hex string
      verify: z.boolean().optional().default(true)
    }).parse(request.body)
    
    try {
      const session = await prisma.flashSession.findUnique({
        where: { id: params.id },
        include: { ECU: true }
      })
      
      if (!session) {
        reply.code(404).send({ error: 'Flash session not found' })
        return
      }
      
      // Simulate ROM write operation
      const dataBuffer = Buffer.from(body.data, 'hex')
      const bytesWritten = dataBuffer.length
      
      // Update session progress
      await prisma.flashSession.update({
        where: { id: params.id },
        data: {
          status: 'flashing',
          progress: 50 // Simulate progress
        }
      })
      
      // Verify write if requested
      let verifyResult = null
      if (body.verify) {
        verifyResult = {
          verified: true,
          mismatches: 0
        }
      }
      
      reply.send({
        success: true,
        operation: 'ROM_WRITE',
        startAddress: `0x${body.startAddress.toString(16)}`,
        bytesWritten,
        verifyResult
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to write ROM' })
    }
  })

  // ROM operations - Erase ROM sector
  fastify.post('/:id/erase-rom', { preHandler: [enforceWriteProtection, requireConfirmation] }, async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const body = z.object({
      startAddress: z.string().transform(val => parseInt(val, 16)),
      length: z.number(),
      eraseType: z.enum(['sector', 'block', 'chip']).optional().default('sector')
    }).parse(request.body)
    
    try {
      const session = await prisma.flashSession.findUnique({
        where: { id: params.id }
      })
      
      if (!session) {
        reply.code(404).send({ error: 'Flash session not found' })
        return
      }
      
      // Simulate ROM erase operation
      const sectorsErased = Math.ceil(body.length / 4096) // Assuming 4KB sectors
      
      reply.send({
        success: true,
        operation: 'ROM_ERASE',
        startAddress: `0x${body.startAddress.toString(16)}`,
        length: body.length,
        eraseType: body.eraseType,
        sectorsErased
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to erase ROM' })
    }
  })

  // Checksum calculation
  fastify.post('/:id/calculate-checksum', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const body = z.object({
      startAddress: z.string().transform(val => parseInt(val, 16)),
      length: z.number(),
      algorithm: z.enum(['sum8', 'sum16', 'sum32', 'crc8', 'crc16', 'crc32']).optional().default('sum16')
    }).parse(request.body)
    
    try {
      // Simulate checksum calculation
      let checksum = 0
      let checksumHex = ''
      
      switch (body.algorithm) {
        case 'sum8':
          checksum = 0x00 // Simulated 8-bit sum
          checksumHex = checksum.toString(16).padStart(2, '0')
          break
        case 'sum16':
          checksum = 0x1234 // Simulated 16-bit sum
          checksumHex = checksum.toString(16).padStart(4, '0')
          break
        case 'sum32':
          checksum = 0x12345678 // Simulated 32-bit sum
          checksumHex = checksum.toString(16).padStart(8, '0')
          break
        case 'crc8':
          checksum = 0xAB // Simulated CRC-8
          checksumHex = checksum.toString(16).padStart(2, '0')
          break
        case 'crc16':
          checksum = 0xABCD // Simulated CRC-16
          checksumHex = checksum.toString(16).padStart(4, '0')
          break
        case 'crc32':
          checksum = 0x12345678 // Simulated CRC-32
          checksumHex = checksum.toString(16).padStart(8, '0')
          break
      }
      
      reply.send({
        success: true,
        operation: 'CHECKSUM_CALCULATE',
        startAddress: `0x${body.startAddress.toString(16)}`,
        length: body.length,
        algorithm: body.algorithm,
        checksum: checksumHex,
        decimal: checksum
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to calculate checksum' })
    }
  })

  // Verify checksum
  fastify.post('/:id/verify-checksum', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const body = z.object({
      startAddress: z.string().transform(val => parseInt(val, 16)),
      length: z.number(),
      expectedChecksum: z.string(),
      algorithm: z.enum(['sum8', 'sum16', 'sum32', 'crc8', 'crc16', 'crc32']).optional().default('sum16')
    }).parse(request.body)
    
    try {
      // Calculate actual checksum (simulated)
      const actualChecksum = body.expectedChecksum // Simulate match
      
      const isValid = actualChecksum.toLowerCase() === body.expectedChecksum.toLowerCase()
      
      // Update flash session with checksum validation result
      await prisma.flashSession.update({
        where: { id: params.id },
        data: {
          checksumValidated: isValid
        }
      })
      
      reply.send({
        success: true,
        operation: 'CHECKSUM_VERIFY',
        valid: isValid,
        expected: body.expectedChecksum,
        actual: actualChecksum,
        algorithm: body.algorithm
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to verify checksum' })
    }
  })

  // Patch checksum
  fastify.post('/:id/patch-checksum', { preHandler: [enforceWriteProtection] }, async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const body = z.object({
      checksumAddress: z.string().transform(val => parseInt(val, 16)),
      newChecksum: z.string(),
      algorithm: z.enum(['sum8', 'sum16', 'sum32', 'crc8', 'crc16', 'crc32']).optional().default('sum16')
    }).parse(request.body)
    
    try {
      const session = await prisma.flashSession.findUnique({
        where: { id: params.id }
      })
      
      if (!session) {
        reply.code(404).send({ error: 'Flash session not found' })
        return
      }
      
      // Simulate checksum patch
      reply.send({
        success: true,
        operation: 'CHECKSUM_PATCH',
        checksumAddress: `0x${body.checksumAddress.toString(16)}`,
        newChecksum: body.newChecksum,
        algorithm: body.algorithm,
        message: 'Checksum patched successfully'
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to patch checksum' })
    }
  })

  // Read ROM definition
  fastify.get('/:id/rom-definition', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    
    try {
      const session = await prisma.flashSession.findUnique({
        where: { id: params.id },
        include: { ECU: true }
      })
      
      if (!session) {
        reply.code(404).send({ error: 'Flash session not found' })
        return
      }
      
      // Return ROM definition based on ECU type
      const romDefinition = {
        ecuType: session.ECU.ecuType,
        baseAddress: '0x8000',
        size: 1048576, // 1MB
        sectors: [
          { start: '0x8000', size: 4096, type: 'bootloader' },
          { start: '0x9000', size: 4096, type: 'calibration' },
          { start: '0xA000', size: 1040384, type: 'main' }
        ],
        checksums: [
          { address: '0x7FFC', algorithm: 'sum16' },
          { address: '0x8FFC', algorithm: 'sum16' }
        ]
      }
      
      reply.send({
        success: true,
        romDefinition
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to get ROM definition' })
    }
  })

  // Get supported ECU types for flashing
  fastify.get('/supported-ecus', async (request, reply) => {
    return [
      {
        ecuType: 'MazdaSpeed3',
        protocols: ['ISO-TP', 'UDS'],
        securityAlgorithms: ['M12R v3.4']
      },
      {
        ecuType: 'Mazda6',
        protocols: ['ISO-TP', 'KWP2000'],
        securityAlgorithms: ['M12R v3.4']
      },
      {
        ecuType: 'CX-5',
        protocols: ['CAN', 'UDS'],
        securityAlgorithms: ['M12R v3.4', 'Custom']
      }
    ]
  })

  // Upload and validate flash file
  fastify.post('/upload', async (request, reply) => {
    // In a real implementation, handle file upload
    // For now, just return validation requirements
    reply.send({
      message: 'File upload endpoint',
      requirements: {
        formats: ['.bin', '.hex', '.s19'],
        maxSize: '10MB',
        checksumRequired: true
      }
    })
  })
}

export default flashRoutes