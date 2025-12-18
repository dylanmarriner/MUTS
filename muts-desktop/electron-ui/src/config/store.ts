/**
 * Local configuration store for MUTS
 * Persists operator mode, technician, and other settings
 */

import { app } from 'electron';
import { promises as fs } from 'fs';
import path from 'path';
import { z } from 'zod';

// Configuration schema
const ConfigSchema = z.object({
  operatorMode: z.enum(['dev', 'workshop', 'lab']).default('dev'),
  technicianId: z.string().optional(),
  lastSelectedTechnician: z.string().optional(),
  requireModeSelection: z.boolean().default(true),
  configVersion: z.string().default('1.0.0'),
});

export type Config = z.infer<typeof ConfigSchema>;

class ConfigStore {
  private configPath: string;
  private config: Config = {
    operatorMode: 'dev',
    requireModeSelection: true,
    configVersion: '1.0.0',
  };

  constructor() {
    // Store config in user data directory
    const userDataPath = app.getPath('userData');
    this.configPath = path.join(userDataPath, 'muts-config.json');
  }

  /**
   * Load configuration from disk
   */
  async load(): Promise<Config> {
    try {
      const data = await fs.readFile(this.configPath, 'utf-8');
      const parsed = JSON.parse(data);
      
      // Validate and merge with defaults
      this.config = ConfigSchema.parse(parsed);
      return this.config;
    } catch (error) {
      // File doesn't exist or is invalid, use defaults
      console.log('Config file not found or invalid, using defaults');
      this.config = ConfigSchema.parse({});
      await this.save();
      return this.config;
    }
  }

  /**
   * Save configuration to disk
   */
  async save(): Promise<void> {
    try {
      // Ensure directory exists
      await fs.mkdir(path.dirname(this.configPath), { recursive: true });
      
      // Write config file
      await fs.writeFile(
        this.configPath,
        JSON.stringify(this.config, null, 2),
        'utf-8'
      );
    } catch (error) {
      console.error('Failed to save config:', error);
      throw error;
    }
  }

  /**
   * Get current configuration
   */
  get(): Config {
    return { ...this.config };
  }

  /**
   * Update configuration
   */
  async update(updates: Partial<Config>): Promise<void> {
    this.config = { ...this.config, ...updates };
    await this.save();
  }

  /**
   * Set operator mode
   */
  async setOperatorMode(mode: 'dev' | 'workshop' | 'lab'): Promise<void> {
    await this.update({ operatorMode: mode });
  }

  /**
   * Get operator mode
   */
  getOperatorMode(): 'dev' | 'workshop' | 'lab' {
    return this.config.operatorMode;
  }

  /**
   * Set current technician
   */
  async setTechnician(technicianId: string): Promise<void> {
    await this.update({ 
      technicianId,
      lastSelectedTechnician: technicianId 
    });
  }

  /**
   * Get current technician
   */
  getTechnician(): string | undefined {
    return this.config.technicianId;
  }

  /**
   * Clear technician (for logout)
   */
  async clearTechnician(): Promise<void> {
    await this.update({ technicianId: undefined });
  }

  /**
   * Skip mode selection on next startup
   */
  async skipModeSelection(skip: boolean = true): Promise<void> {
    await this.update({ requireModeSelection: !skip });
  }

  /**
   * Check if mode selection is required
   */
  isModeSelectionRequired(): boolean {
    return this.config.requireModeSelection;
  }

  /**
   * Reset configuration to defaults
   */
  async reset(): Promise<void> {
    this.config = ConfigSchema.parse({});
    await this.save();
  }
}

// Export singleton instance
export const configStore = new ConfigStore();
