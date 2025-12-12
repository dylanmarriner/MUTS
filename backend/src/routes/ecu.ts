import { FastifyPluginAsync } from 'fastify'
import { z } from 'zod'
import { prisma } from '../index'

const ecuSchema = z.object({
  vin: z.string().optional(),
  ecuType: z.string(),
  protocol: z.enum(['J2534', 'ISO-TP', 'UDS', 'KWP2000', 'CAN']),
  firmwareVersion: z.string().optional(),
  hardwareVersion: z.string().optional(),
  serialNumber: z.string().optional(),
  securityAlgorithm: z.string().optional()
})

const ecuRoutes: FastifyPluginAsync = async (fastify) => {
  // Get all ECUs
  fastify.get('/', async (request, reply) => {
    const ecus = await prisma.eCU.findMany({
      include: {
        diagnosticSessions: {
          select: {
            id: true,
            startTime: true,
            endTime: true,
            status: true
          }
        },
        tuningProfiles: {
          select: {
            id: true,
            name: true,
            isActive: true,
            isBase: true
          }
        },
        _count: {
          select: {
            flashSessions: true,
            logs: true
          }
        }
      }
    })
    return ecus
  })

  // Get ECU by ID
  fastify.get('/:id', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    
    const ecu = await prisma.eCU.findUnique({
      where: { id: params.id },
      include: {
        diagnosticSessions: true,
        tuningProfiles: true,
        flashSessions: true,
        securitySessions: true,
        logs: true,
        torqueAdvisories: true,
        swasConfigurations: true
      }
    })

    if (!ecu) {
      reply.code(404).send({ error: 'ECU not found' })
      return
    }

    return ecu
  })

  // Create new ECU
  fastify.post('/', async (request, reply) => {
    const data = ecuSchema.parse(request.body)
    
    try {
      const ecu = await prisma.eCU.create({
        data: {
          vin: data.vin,
          ecuType: data.ecuType,
          protocol: data.protocol,
          firmwareVersion: data.firmwareVersion,
          hardwareVersion: data.hardwareVersion,
          serialNumber: data.serialNumber,
          securityAlgorithm: data.securityAlgorithm
        }
      })
      reply.code(201).send(ecu)
    } catch (error: any) {
      if (error.code === 'P2002') {
        reply.code(409).send({ error: 'ECU with this VIN or serial number already exists' })
        return
      }
      throw error
    }
  })

  // Update ECU
  fastify.put('/:id', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const data = ecuSchema.partial().parse(request.body)
    
    try {
      const ecu = await prisma.eCU.update({
        where: { id: params.id },
        data: {
          ...data,
          protocol: data.protocol || 'CAN'
        }
      })
      return ecu
    } catch (error: any) {
      if (error.code === 'P2025') {
        reply.code(404).send({ error: 'ECU not found' })
        return
      }
      throw error
    }
  })

  // Delete ECU
  fastify.delete('/:id', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    
    try {
      await prisma.eCU.delete({
        where: { id: params.id }
      })
      reply.code(204).send()
    } catch (error: any) {
      if (error.code === 'P2025') {
        reply.code(404).send({ error: 'ECU not found' })
        return
      }
      throw error
    }
  })

  // Get ECU protocols
  fastify.get('/protocols/list', async (request, reply) => {
    return ['J2534', 'ISO-TP', 'UDS', 'KWP2000', 'CAN']
  })

  // Get ECU types
  fastify.get('/types/list', async (request, reply) => {
    const ecus = await prisma.eCU.findMany({
      select: { ecuType: true },
      distinct: ['ecuType']
    })
    return ecus.map((e: any) => e.ecuType)
  })

  // CAN communication features
  fastify.post('/:id/can-connect', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const body = z.object({
      interface: z.string().optional().default('socketcan'),
      channel: z.string().optional().default('can0'),
      bitrate: z.number().optional().default(500000)
    }).parse(request.body)
    
    try {
      const ecu = await prisma.eCU.findUnique({
        where: { id: params.id }
      })
      
      if (!ecu) {
        reply.code(404).send({ error: 'ECU not found' })
        return
      }
      
      // Simulate CAN connection
      // In real implementation, this would initialize CAN interface
      reply.send({
        success: true,
        message: 'CAN interface connected',
        interface: body.interface,
        channel: body.channel,
        bitrate: body.bitrate,
        ecuProtocol: ecu.protocol
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to connect CAN interface' })
    }
  })

  // Send CAN message
  fastify.post('/:id/can-send', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const body = z.object({
      arbitrationId: z.string().transform(val => parseInt(val, 16)),
      data: z.string().transform(val => Buffer.from(val, 'hex')),
      extendedId: z.boolean().optional().default(false),
      technicianId: z.string().optional(),
      jobId: z.string().optional()
    }).parse(request.body)
    
    // CRITICAL SAFETY CHECK: Check operator mode for write permissions
    const { operatorMode } = await import('../modules/operator-modes');
    const writeCheck = operatorMode.validateEcuWrite('canSend');
    
    if (!writeCheck.allowed) {
      reply.code(403).send({ 
        error: 'CAN write operations disabled',
        message: writeCheck.reason
      })
      return
    }
    
    // CRITICAL: Require technician attribution in non-DEV modes
    if (operatorMode.getCurrentMode() !== 'dev' && !body.technicianId) {
      reply.code(403).send({ 
        error: 'Technician attribution required for CAN write operations'
      })
      return
    }
    
    try {
      // Log the CAN send operation if job tracking is available
      if (body.jobId && body.technicianId) {
        const { getJobTrackingService } = await import('../modules/job-tracking');
        const jobService = getJobTrackingService(prisma);
        await jobService.logDiagnostic(
          body.jobId,
          body.technicianId,
          `CAN message sent: ID 0x${body.arbitrationId.toString(16)}`,
          {
            arbitrationId: body.arbitrationId,
            dataLength: body.data.length,
            extendedId: body.extendedId,
          }
        );
      }
      
      // Simulate sending CAN message
      // In real implementation, this would send via CAN interface
      reply.send({
        success: true,
        message: 'CAN message sent',
        arbitrationId: `0x${body.arbitrationId.toString(16)}`,
        dataLength: body.data.length,
        timestamp: new Date().toISOString()
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to send CAN message' })
    }
  })

  // Receive CAN messages
  fastify.get('/:id/can-receive', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const query = z.object({
      timeout: z.number().optional().default(1000),
      filter: z.string().optional()
    }).parse(request.query)
    
    try {
      // Simulate receiving CAN messages
      // In real implementation, this would read from CAN interface
      const messages = [
        {
          arbitrationId: '0x7E8',
          data: '6210400000000000',
          extendedId: false,
          timestamp: new Date().toISOString()
        },
        {
          arbitrationId: '0x7E0',
          data: '0210030000000000',
          extendedId: false,
          timestamp: new Date().toISOString()
        }
      ]
      
      reply.send({
        success: true,
        messages,
        count: messages.length
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to receive CAN messages' })
    }
  })

  // J2534 interface communication
  fastify.post('/:id/j2534-connect', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const body = z.object({
      deviceId: z.number().optional(),
      protocol: z.enum(['ISO15765', 'ISO9141', 'ISO14230', 'J1850PWM', 'J1850VPW', 'CAN', 'ISO22857'])
    }).parse(request.body)
    
    try {
      const ecu = await prisma.eCU.findUnique({
        where: { id: params.id }
      })
      
      if (!ecu) {
        reply.code(404).send({ error: 'ECU not found' })
        return
      }
      
      // Simulate J2534 connection
      reply.send({
        success: true,
        message: 'J2534 device connected',
        deviceId: body.deviceId || 0,
        protocol: body.protocol,
        ecuType: ecu.ecuType
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to connect J2534 device' })
    }
  })

  // ISO-TP communication
  fastify.post('/:id/isotp-communicate', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const body = z.object({
      serviceId: z.string().transform(val => parseInt(val, 16)),
      data: z.string().optional().transform(val => val ? Buffer.from(val, 'hex') : Buffer.alloc(0)),
      blockSize: z.number().optional().default(8),
      separationTime: z.number().optional().default(0)
    }).parse(request.body)
    
    try {
      // Simulate ISO-TP communication
      // In real implementation, this would handle ISO-TP protocol
      const response = {
        serviceId: '0x62', // Response to 0x22 request
        data: 'F1900123456789ABCDEF', // Example response data
        length: 10
      }
      
      reply.send({
        success: true,
        request: {
          serviceId: `0x${body.serviceId.toString(16)}`,
          dataLength: body.data.length
        },
        response,
        protocol: 'ISO-TP'
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'ISO-TP communication failed' })
    }
  })

  // UDS (Unified Diagnostic Services)
  fastify.post('/:id/uds-communicate', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const body = z.object({
      service: z.string(), // e.g., 'ReadDataByIdentifier', 'WriteDataByIdentifier'
      subfunction: z.number().optional(),
      dataIdentifier: z.string().optional(),
      data: z.string().optional(),
      technicianId: z.string().optional(),
      jobId: z.string().optional()
    }).parse(request.body)
    
    // CRITICAL SAFETY CHECK: Check operator mode for write permissions
    if (body.service === 'WriteDataByIdentifier') {
      const { operatorMode } = await import('../modules/operator-modes');
      const writeCheck = operatorMode.validateEcuWrite('udsWrite');
      
      if (!writeCheck.allowed) {
        reply.code(403).send({ 
          error: 'UDS write operations disabled',
          message: writeCheck.reason
        })
        return
      }
      
      // CRITICAL: Require technician attribution in non-DEV modes
      if (operatorMode.getCurrentMode() !== 'dev' && !body.technicianId) {
        reply.code(403).send({ 
          error: 'Technician attribution required for UDS write operations'
        })
        return
      }
    }
    
    try {
      // Simulate UDS communication
      let response: any = {}
      
      switch (body.service) {
        case 'ReadDataByIdentifier':
          response = {
            service: '62', // Positive response
            dataIdentifier: body.dataIdentifier,
            data: '1234567890ABCDEF'
          }
          break
        case 'WriteDataByIdentifier':
          // Log the write operation if job tracking is available
          if (body.jobId && body.technicianId) {
            const { getJobTrackingService } = await import('../modules/job-tracking');
            const jobService = getJobTrackingService(prisma);
            await jobService.logDiagnostic(
              body.jobId,
              body.technicianId,
              `UDS WriteDataByIdentifier: ${body.dataIdentifier}`,
              {
                dataIdentifier: body.dataIdentifier,
                data: body.data,
              }
            );
          }
          
          response = {
            service: '6E', // Positive response
            dataIdentifier: body.dataIdentifier
          }
          break
        case 'SessionControl':
          response = {
            service: '50', // Positive response
            subfunction: body.subfunction,
            parameterRecord: '00'
          }
          break
        case 'SecurityAccess':
          response = {
            service: '67', // Positive response
            subfunction: body.subfunction,
            securitySeed: '12345678'
          }
          break
        default:
          response = {
            service: '7F', // Negative response
            error: '31' // Service not supported
          }
      }
      
      reply.send({
        success: true,
        request: body,
        response,
        protocol: 'UDS'
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'UDS communication failed' })
    }
  })

  // KWP2000 communication
  fastify.post('/:id/kwp2000-communicate', async (request, reply) => {
    const params = z.object({ id: z.string() }).parse(request.params)
    const body = z.object({
      serviceId: z.string().transform(val => parseInt(val, 16)),
      data: z.string().optional().transform(val => val ? Buffer.from(val, 'hex') : Buffer.alloc(0))
    }).parse(request.body)
    
    try {
      // Simulate KWP2000 communication
      const response = {
        serviceId: `0x${(body.serviceId | 0x40).toString(16)}`, // Positive response bit set
        data: body.data.toString('hex').padEnd(16, '0').substring(0, 16) // Echo back data
      }
      
      reply.send({
        success: true,
        request: {
          serviceId: `0x${body.serviceId.toString(16)}`,
          dataLength: body.data.length
        },
        response,
        protocol: 'KWP2000'
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'KWP2000 communication failed' })
    }
  })
}

export default ecuRoutes