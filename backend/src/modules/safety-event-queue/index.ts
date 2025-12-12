/**
 * Durable Safety Event Queue
 * Ensures safety events are never dropped and can be replayed
 */

import { EventEmitter } from 'events';
import { PrismaClient } from '@prisma/client';

export interface SafetyEvent {
  id: string;
  type: 'violation' | 'sessionCreated' | 'sessionExpired' | 'sessionArmed' | 'sessionApplied';
  data: any;
  timestamp: Date;
  delivered: boolean;
  deliveryAttempts: number;
}

export class SafetyEventQueue extends EventEmitter {
  private prisma: PrismaClient;
  private processing: boolean = false;
  private batchSize: number = 100;
  private maxRetries: number = 3;
  private retryDelay: number = 1000; // 1 second

  constructor(prisma: PrismaClient) {
    super();
    this.prisma = prisma;
  }

  /**
   * Add a safety event to the durable queue
   */
  async addEvent(type: SafetyEvent['type'], data: any): Promise<void> {
    const event: Omit<SafetyEvent, 'delivered' | 'deliveryAttempts'> = {
      id: `safety_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type,
      data,
      timestamp: new Date(),
    };

    // Store in database for durability
    await this.prisma.safetyEvent.create({
      data: {
        eventId: event.id,
        eventType: event.type,
        eventData: JSON.stringify(event.data),
        timestamp: event.timestamp,
        delivered: false,
        deliveryAttempts: 0,
      },
    });

    // Emit for immediate delivery to connected clients
    this.emit('safetyEvent', event);
  }

  /**
   * Get undelivered events for replay
   */
  async getUndeliveredEvents(limit: number = 100): Promise<SafetyEvent[]> {
    const events = await this.prisma.safetyEvent.findMany({
      where: {
        delivered: false,
        deliveryAttempts: {
          lt: this.maxRetries,
        },
      },
      orderBy: {
        timestamp: 'asc',
      },
      take: limit,
    });

    return events.map(e => ({
      id: e.eventId,
      type: e.eventType as SafetyEvent['type'],
      data: JSON.parse(e.eventData),
      timestamp: e.timestamp,
      delivered: e.delivered,
      deliveryAttempts: e.deliveryAttempts,
    }));
  }

  /**
   * Mark events as delivered
   */
  async markDelivered(eventIds: string[]): Promise<void> {
    await this.prisma.safetyEvent.updateMany({
      where: {
        eventId: {
          in: eventIds,
        },
      },
      data: {
        delivered: true,
        deliveredAt: new Date(),
      },
    });
  }

  /**
   * Increment delivery attempts for failed events
   */
  async incrementDeliveryAttempts(eventIds: string[]): Promise<void> {
    await this.prisma.safetyEvent.updateMany({
      where: {
        eventId: {
          in: eventIds,
        },
      },
      data: {
        deliveryAttempts: {
          increment: 1,
        },
        lastDeliveryAttempt: new Date(),
      },
    });
  }

  /**
   * Start processing the queue for delivery
   */
  async startProcessing(): Promise<void> {
    if (this.processing) return;
    
    this.processing = true;
    
    while (this.processing) {
      try {
        const events = await this.getUndeliveredEvents(this.batchSize);
        
        if (events.length === 0) {
          await new Promise(resolve => setTimeout(resolve, 100));
          continue;
        }

        // Emit events for delivery
        const deliveredIds: string[] = [];
        const failedIds: string[] = [];

        for (const event of events) {
          try {
            this.emit('safetyEvent', event);
            deliveredIds.push(event.id);
          } catch (error) {
            console.error('Failed to deliver safety event:', error);
            failedIds.push(event.id);
          }
        }

        // Update delivery status
        if (deliveredIds.length > 0) {
          await this.markDelivered(deliveredIds);
        }
        
        if (failedIds.length > 0) {
          await this.incrementDeliveryAttempts(failedIds);
        }

        // Brief pause between batches
        await new Promise(resolve => setTimeout(resolve, 10));
      } catch (error) {
        console.error('Error processing safety event queue:', error);
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
  }

  /**
   * Stop processing the queue
   */
  stopProcessing(): void {
    this.processing = false;
  }

  /**
   * Clean up old delivered events
   */
  async cleanup(olderThanDays: number = 7): Promise<void> {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - olderThanDays);

    await this.prisma.safetyEvent.deleteMany({
      where: {
        delivered: true,
        deliveredAt: {
          lt: cutoffDate,
        },
      },
    });
  }
}

// Singleton instance
let queueInstance: SafetyEventQueue | null = null;

export function getSafetyEventQueue(prisma: PrismaClient): SafetyEventQueue {
  if (!queueInstance) {
    queueInstance = new SafetyEventQueue(prisma);
  }
  return queueInstance;
}
