import { FastifyPluginAsync } from 'fastify'
import { z } from 'zod'
import { prisma } from '../index'

const agentStatusSchema = z.object({
  agentName: z.string(),
  status: z.enum(['idle', 'running', 'error', 'completed']),
  currentTask: z.string().optional(),
  metadata: z.any().optional()
})

const agentRoutes: FastifyPluginAsync = async (fastify) => {
  // Get all agent statuses
  fastify.get('/', async (request, reply) => {
    const agents = await prisma.agentStatus.findMany({
      orderBy: {
        lastUpdate: 'desc'
      }
    })
    
    return agents
  })

  // Get agent status by name
  fastify.get('/:name', async (request, reply) => {
    const params = z.object({ name: z.string() }).parse(request.params)
    
    const agent = await prisma.agentStatus.findUnique({
      where: { agentName: params.name }
    })

    if (!agent) {
      reply.code(404).send({ error: 'Agent not found' })
      return
    }

    return agent
  })

  // Update or create agent status
  fastify.put('/:name', async (request, reply) => {
    const params = z.object({ name: z.string() }).parse(request.params)
    const data = agentStatusSchema.partial().omit({ agentName: true }).parse(request.body)
    
    const agent = await prisma.agentStatus.upsert({
      where: { agentName: params.name },
      update: {
        ...data,
        lastUpdate: new Date()
      },
      create: {
        agentName: params.name,
        status: data.status || 'idle',
        currentTask: data.currentTask,
        metadata: data.metadata,
        lastUpdate: new Date()
      }
    })
    
    return agent
  })

  // Delete agent status
  fastify.delete('/:name', async (request, reply) => {
    const params = z.object({ name: z.string() }).parse(request.params)
    
    try {
      await prisma.agentStatus.delete({
        where: { agentName: params.name }
      })
      reply.code(204).send()
    } catch (error: any) {
      if (error.code === 'P2025') {
        reply.code(404).send({ error: 'Agent not found' })
        return
      }
      throw error
    }
  })

  // Start agent task
  fastify.post('/:name/start-task', async (request, reply) => {
    const params = z.object({ name: z.string() }).parse(request.params)
    const body = z.object({
      task: z.string(),
      parameters: z.any().optional()
    }).parse(request.body)
    
    try {
      const agentStatus = await prisma.agentStatus.create({
        data: {
          agentName: params.name,
          status: 'running',
          currentTask: body.task,
          metadata: JSON.stringify({
            taskStarted: new Date().toISOString(),
            parameters: body.parameters
          }),
          lastUpdate: new Date()
        }
      })
      
      // In real implementation, would trigger actual agent task
      reply.send({
        ...agentStatus,
        message: `Task started for agent ${params.name}`,
        task: body.task
      })
    } catch (error: any) {
      if (error.code === 'P2025') {
        reply.code(404).send({ error: 'Agent not found' })
        return
      }
      throw error
    }
  })

  // Complete agent task
  fastify.post('/:name/complete-task', async (request, reply) => {
    const params = z.object({ name: z.string() }).parse(request.params)
    const body = z.object({
      result: z.any().optional(),
      error: z.string().optional()
    }).parse(request.body)
    
    try {
      const agent = await prisma.agentStatus.findUnique({
        where: { agentName: params.name }
      })
      
      if (!agent) {
        reply.code(404).send({ error: 'Agent not found' })
        return
      }
      
      const updateData: any = {
        status: body.error ? 'error' : 'completed',
        currentTask: null,
        lastUpdate: new Date()
      }
      
      if (agent.metadata) {
        updateData.metadata = JSON.stringify({
          ...JSON.parse(agent.metadata),
          taskCompleted: new Date().toISOString(),
          result: body.result,
          error: body.error
        })
      }
      
      const updatedAgent = await prisma.agentStatus.update({
        where: { agentName: params.name },
        data: updateData
      })
      
      reply.send({
        ...updatedAgent,
        message: `Task ${body.error ? 'failed' : 'completed'} for agent ${params.name}`
      })
    } catch (error: any) {
      reply.code(500).send({ error: 'Failed to complete task' })
    }
  })

  // Get agent coordination status
  fastify.get('/coordination/status', async (request, reply) => {
    const agents = await prisma.agentStatus.findMany({
      orderBy: { agentName: 'asc' }
    })
    
    const status = {
      totalAgents: agents.length,
      running: agents.filter((a: any) => a.status === 'running').length,
      idle: agents.filter((a: any) => a.status === 'idle').length,
      error: agents.filter((a: any) => a.status === 'error').length,
      completed: agents.filter((a: any) => a.status === 'completed').length,
      agents: agents.map((a: any) => ({
        name: a.agentName,
        status: a.status,
        currentTask: a.currentTask,
        lastUpdate: a.lastUpdate
      }))
    }
    
    reply.send(status)
  })

  // Get available agents
  fastify.get('/list/available', async (request, reply) => {
    const availableAgents = [
      {
        name: 'ECUCommsAgent',
        description: 'Handles communication via J2534, ISO-TP, UDS, KWP2000',
        capabilities: ['ecu_detection', 'protocol_negotiation', 'data_transfer']
      },
      {
        name: 'DiagnosticsAgent',
        description: 'Runs full system scans, retrieves DTCs, freeze frames',
        capabilities: ['dtc_reading', 'live_data', 'freeze_frames', 'system_scan']
      },
      {
        name: 'TuningAgent',
        description: 'Evaluates and edits tuning profiles, ensures safe configuration',
        capabilities: ['map_editing', 'profile_validation', 'safety_checks']
      },
      {
        name: 'SafetyAgent',
        description: 'Enforces safety_limits, blocks invalid flashes or dangerous tunes',
        capabilities: ['limit_validation', 'risk_assessment', 'blocking']
      },
      {
        name: 'FlashAgent',
        description: 'Manages ECU flashing, rollback, verification, checksum patching',
        capabilities: ['flashing', 'verification', 'rollback', 'checksum']
      },
      {
        name: 'LogAnalysisAgent',
        description: 'Processes driving logs, dyno calculations, torque predictions',
        capabilities: ['log_processing', 'dyno_simulation', 'torque_prediction']
      },
      {
        name: 'TorqueAdvisorAgent',
        description: 'Suggests per-gear torque limits based on logs',
        capabilities: ['torque_analysis', 'limit_recommendation', 'safety_margin']
      },
      {
        name: 'SWASAgent',
        description: 'Manages steering-angle-based torque reduction',
        capabilities: ['angle_monitoring', 'torque_reduction', 'curve_management']
      },
      {
        name: 'UIOrchestratorAgent',
        description: 'Coordinates updates between backend agents and the GUI',
        capabilities: ['agent_coordination', 'ui_updates', 'event_broadcasting']
      }
    ]
    
    // Add current status if available
    const currentStatuses = await prisma.agentStatus.findMany({
      where: {
        agentName: {
          in: availableAgents.map(a => a.name)
        }
      }
    })
    
    const statusMap = currentStatuses.reduce((acc: any, status: any) => {
      acc[status.agentName] = status
      return acc
    }, {} as Record<string, any>)
    
    const agentsWithStatus = availableAgents.map(agent => ({
      ...agent,
      currentStatus: statusMap[agent.name] || {
        status: 'idle',
        lastUpdate: null
      }
    }))
    
    reply.send(agentsWithStatus)
  })

  // Reset all agents
  fastify.post('/reset-all', async (request, reply) => {
    await prisma.agentStatus.updateMany({
      data: {
        status: 'idle',
        currentTask: null,
        metadata: null,
        lastUpdate: new Date()
      }
    })
    
    reply.send({
      message: 'All agents reset to idle state'
    })
  })

  // Get agent task history (would require additional table in real implementation)
  fastify.get('/:name/history', async (request, reply) => {
    const params = z.object({ name: z.string() }).parse(request.params)
    const query = z.object({
      limit: z.string().optional().transform(Number),
      status: z.enum(['idle', 'running', 'error', 'completed']).optional()
    }).parse(request.query)
    
    // In real implementation, would query task history table
    reply.send({
      agentName: params.name,
      history: [],
      message: 'Task history not implemented - would require additional table'
    })
  })
}

export default agentRoutes