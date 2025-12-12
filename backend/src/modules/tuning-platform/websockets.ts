/**
 * WebSocket handlers for Unified Tuning Platform
 * Provides real-time streams for telemetry, safety, and engine-specific updates
 */

import { FastifyInstance, FastifyRequest } from 'fastify'
import { WebSocket } from '@fastify/websocket'
import { SafetyOrchestrator } from './safety-orchestrator'
import { VersaEngine } from './engines/versa-engine'
import { CobbEngine } from './engines/cobb-engine'
import { MdsEngine } from './engines/mds-engine'

// Initialize engines
const versaEngine = new VersaEngine()
const cobbEngine = new CobbEngine()
const mdsEngine = new MdsEngine()

// Map engine IDs to instances
const engines = {
  versa: versaEngine,
  cobb: cobbEngine,
  mds: mdsEngine
}

/**
 * Telemetry stream - broadcasts real-time sensor data
 */
export async function telemetryStream(connection: WebSocket, req: FastifyRequest) {
  console.log('WebSocket telemetry client connected')
  
  // Send initial status
  connection.send(JSON.stringify({
    type: 'status',
    data: {
      connected: true,
      timestamp: new Date().toISOString()
    }
  }))

  // Simulate telemetry data (in real implementation, this would come from ECU)
  const telemetryInterval = setInterval(() => {
    const telemetry = {
      rpm: Math.random() * 8000,
      boost: Math.random() * 30,
      afr: 14.7 + (Math.random() - 0.5) * 2,
      timing: Math.random() * 40,
      coolant: 80 + Math.random() * 40,
      iat: 20 + Math.random() * 60,
      knock: Math.random() > 0.95 ? 1 : 0,
      timestamp: new Date().toISOString()
    }

    connection.send(JSON.stringify({
      type: 'telemetry',
      data: telemetry
    }))
  }, 100)

  connection.on('message', message => {
    try {
      const data = JSON.parse(message.toString())
      console.log('Received telemetry command:', data)
      
      // Handle commands like subscribe/unsubscribe to specific sensors
      if (data.command === 'subscribe') {
        connection.send(JSON.stringify({
          type: 'subscribed',
          sensors: data.sensors || ['all']
        }))
      }
    } catch (error) {
      console.error('Invalid telemetry message:', error)
    }
  })

  connection.on('close', () => {
    console.log('WebSocket telemetry client disconnected')
    clearInterval(telemetryInterval)
  })
}

/**
 * Safety stream - broadcasts safety violations and session events
 */
export async function safetyStream(connection: WebSocket, req: FastifyRequest) {
  console.log('WebSocket safety client connected')
  
  const safetyOrchestrator = new SafetyOrchestrator()

  // Send initial safety status
  connection.send(JSON.stringify({
    type: 'safetyStatus',
    data: {
      level: safetyOrchestrator.getCurrentLevel(),
      armed: safetyOrchestrator.isArmed(),
      activeSessions: safetyOrchestrator.getActiveSessionsCount(),
      timestamp: new Date().toISOString()
    }
  }))

  // Listen to safety events
  const onSafetyViolation = (data: any) => {
    connection.send(JSON.stringify({
      type: 'safetyViolation',
      data: {
        ...data,
        timestamp: new Date().toISOString()
      }
    }))
  }

  const onSessionCreated = (session: any) => {
    connection.send(JSON.stringify({
      type: 'sessionCreated',
      data: {
        ...session,
        timestamp: new Date().toISOString()
      }
    }))
  }

  const onSessionExpired = (sessionId: string) => {
    connection.send(JSON.stringify({
      type: 'sessionExpired',
      data: {
        sessionId,
        timestamp: new Date().toISOString()
      }
    }))
  }

  // Register event listeners (in real implementation, these would be on the actual orchestrator)
  // safetyOrchestrator.on('safetyViolation', onSafetyViolation)
  // safetyOrchestrator.on('sessionCreated', onSessionCreated)
  // safetyOrchestrator.on('sessionExpired', onSessionExpired)

  connection.on('message', message => {
    try {
      const data = JSON.parse(message.toString())
      console.log('Received safety command:', data)
      
      if (data.command === 'arm') {
        connection.send(JSON.stringify({
          type: 'armStatus',
          data: {
            success: true,
            timestamp: new Date().toISOString()
          }
        }))
      } else if (data.command === 'disarm') {
        connection.send(JSON.stringify({
          type: 'disarmStatus',
          data: {
            success: true,
            timestamp: new Date().toISOString()
          }
        }))
      }
    } catch (error) {
      console.error('Invalid safety message:', error)
    }
  })

  connection.on('close', () => {
    console.log('WebSocket safety client disconnected')
    // Remove event listeners
    // safetyOrchestrator.off('safetyViolation', onSafetyViolation)
    // safetyOrchestrator.off('sessionCreated', onSessionCreated)
    // safetyOrchestrator.off('sessionExpired', onSessionExpired)
  })
}

/**
 * Engine-specific tuning stream
 */
export async function engineTuningStream(connection: WebSocket, req: FastifyRequest) {
  const params = req.params as { engine: string }
  const query = req.query as { profileId?: string }
  const engineId = params.engine
  const profileId = query.profileId
  const engine = engines[engineId as keyof typeof engines]

  if (!engine) {
    connection.send(JSON.stringify({
      type: 'error',
      data: {
        message: `Engine ${engineId} not found`,
        timestamp: new Date().toISOString()
      }
    }))
    connection.close()
    return
  }

  console.log(`WebSocket tuning client connected for engine: ${engineId}`)

  // Send initial engine status
  connection.send(JSON.stringify({
    type: 'engineStatus',
    data: {
      engine: engineId,
      connected: true,
      capabilities: engine.getCapabilities(),
      timestamp: new Date().toISOString()
    }
  }))

  // Subscribe to engine telemetry if supported
  if (engine.subscribeTelemetry) {
    engine.subscribeTelemetry((data: any) => {
      connection.send(JSON.stringify({
        type: 'engineTelemetry',
        engine: engineId,
        data: {
          ...data,
          timestamp: new Date().toISOString()
        }
      }))
    })
  }

  connection.on('message', message => {
    try {
      const data = JSON.parse(message.toString())
      console.log(`Received tuning command for ${engineId}:`, data)

      // Handle engine-specific commands
      switch (data.command) {
        case 'getMaps':
          engine.listMaps(profileId || '').then(maps => {
            connection.send(JSON.stringify({
              type: 'maps',
              engine: engineId,
              data: maps
            }))
          })
          break

        case 'getMap':
          engine.getMap(data.mapId).then(map => {
            connection.send(JSON.stringify({
              type: 'map',
              engine: engineId,
              data: map
            }))
          })
          break

        case 'updateMap':
          engine.updateMap(data.mapId, data.payload).then(result => {
            connection.send(JSON.stringify({
              type: 'mapUpdated',
              engine: engineId,
              data: result
            }))
          }).catch(error => {
            connection.send(JSON.stringify({
              type: 'error',
              engine: engineId,
              data: { message: error.message }
            }))
          })
          break

        case 'validate':
          engine.validateChanges(data.changeset).then(result => {
            connection.send(JSON.stringify({
              type: 'validationResult',
              engine: engineId,
              data: result
            }))
          })
          break

        case 'simulate':
          engine.simulate(data.changeset).then(result => {
            connection.send(JSON.stringify({
              type: 'simulationResult',
              engine: engineId,
              data: result
            }))
          })
          break
      }
    } catch (error) {
      console.error(`Invalid tuning message for ${engineId}:`, error)
      connection.send(JSON.stringify({
        type: 'error',
        engine: engineId,
        data: { message: 'Invalid message format' }
      }))
    }
  })

  connection.on('close', () => {
    console.log(`WebSocket tuning client disconnected for engine: ${engineId}`)
  })
}

/**
 * Flash progress stream
 */
export async function flashStream(connection: WebSocket, req: FastifyRequest) {
  const params = req.params as { engine: string }
  const engineId = params.engine
  const engine = engines[engineId as keyof typeof engines]

  if (!engine) {
    connection.send(JSON.stringify({
      type: 'error',
      data: {
        message: `Engine ${engineId} not found`,
        timestamp: new Date().toISOString()
      }
    }))
    connection.close()
    return
  }

  console.log(`WebSocket flash client connected for engine: ${engineId}`)

  connection.on('message', message => {
    try {
      const data = JSON.parse(message.toString())
      console.log(`Received flash command for ${engineId}:`, data)

      switch (data.command) {
        case 'prepare':
          engine.buildFlashImage(data.profile || data.changeset).then(image => {
            connection.send(JSON.stringify({
              type: 'flashPrepared',
              engine: engineId,
              data: {
                success: true,
                image: image,
                timestamp: new Date().toISOString()
              }
            }))
          }).catch(error => {
            connection.send(JSON.stringify({
              type: 'error',
              engine: engineId,
              data: { message: error.message }
            }))
          })
          break

        case 'execute':
          // Simulate flash progress
          let progress = 0
          const flashInterval = setInterval(() => {
            progress += Math.random() * 10
            
            if (progress >= 100) {
              progress = 100
              clearInterval(flashInterval)
              
              connection.send(JSON.stringify({
                type: 'flashComplete',
                engine: engineId,
                data: {
                  success: true,
                  checksum: '0x' + Math.random().toString(16).substr(2, 8),
                  timestamp: new Date().toISOString()
                }
              }))
            } else {
              connection.send(JSON.stringify({
                type: 'flashProgress',
                engine: engineId,
                data: {
                  progress: Math.round(progress),
                  stage: progress < 30 ? 'Preparing' : progress < 70 ? 'Writing' : 'Verifying',
                  timestamp: new Date().toISOString()
                }
              }))
            }
          }, 500)
          break

        case 'abort':
          connection.send(JSON.stringify({
            type: 'flashAborted',
            engine: engineId,
            data: {
              message: 'Flash operation aborted',
              timestamp: new Date().toISOString()
            }
          }))
          break
      }
    } catch (error) {
      console.error(`Invalid flash message for ${engineId}:`, error)
    }
  })

  connection.on('close', () => {
    console.log(`WebSocket flash client disconnected for engine: ${engineId}`)
  })
}

/**
 * Register all WebSocket routes
 */
export function registerWebSocketRoutes(fastify: FastifyInstance) {
  // Telemetry stream
  fastify.get('/ws/stream/telemetry', { websocket: true }, telemetryStream)

  // Safety stream
  fastify.get('/ws/stream/safety', { websocket: true }, safetyStream)

  // Engine-specific tuning streams
  fastify.get('/ws/stream/tuning/:engine', { websocket: true }, engineTuningStream)

  // Flash progress streams
  fastify.get('/ws/stream/flash/:engine', { websocket: true }, flashStream)

  console.log('WebSocket routes registered for Unified Tuning Platform')
}
