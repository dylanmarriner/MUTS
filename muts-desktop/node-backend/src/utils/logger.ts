/**
 * Logger Utility
 * Provides structured logging for the MUTS backend
 */

import winston from 'winston';
import { app } from 'electron';
import path from 'path';

export class Logger {
  private logger: winston.Logger;

  constructor(label: string) {
    this.logger = winston.createLogger({
      level: 'info',
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.label({ label }),
        winston.format.errors({ stack: true }),
        winston.format.json()
      ),
      defaultMeta: { service: 'muts-backend' },
      transports: [
        // Write to logs directory
        new winston.transports.File({
          filename: path.join(app.getPath('logs'), 'error.log'),
          level: 'error',
        }),
        new winston.transports.File({
          filename: path.join(app.getPath('logs'), 'combined.log'),
        }),
      ],
    });

    // Add console transport in development
    if (process.env.NODE_ENV !== 'production') {
      this.logger.add(new winston.transports.Console({
        format: winston.format.combine(
          winston.format.colorize(),
          winston.format.simple(),
          winston.format.printf(({ level, message, label, timestamp }) => {
            return `${timestamp} [${label}] ${level}: ${message}`;
          })
        )
      }));
    }
  }

  info(message: string, ...args: any[]): void {
    this.logger.info(message, ...args);
  }

  error(message: string, ...args: any[]): void {
    this.logger.error(message, ...args);
  }

  warn(message: string, ...args: any[]): void {
    this.logger.warn(message, ...args);
  }

  debug(message: string, ...args: any[]): void {
    this.logger.debug(message, ...args);
  }
}
