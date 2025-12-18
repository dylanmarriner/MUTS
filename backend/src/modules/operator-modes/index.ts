/**
 * Operator Mode Service
 * Manages runtime operator modes and permissions
 */

import { OperatorMode, OPERATOR_MODE_CONFIGS, OperatorModeRequirements } from './types';

export class OperatorModeService {
  private static instance: OperatorModeService;
  private currentMode: OperatorMode;

  private constructor() {
    // Read mode from environment at startup
    const modeFromEnv = process.env.OPERATOR_MODE?.toLowerCase();
    
    switch (modeFromEnv) {
      case 'dev':
        this.currentMode = OperatorMode.DEV;
        break;
      case 'workshop':
        this.currentMode = OperatorMode.WORKSHOP;
        break;
      case 'lab':
        this.currentMode = OperatorMode.LAB;
        break;
      default:
        console.warn(`Invalid OPERATOR_MODE "${modeFromEnv}", defaulting to DEV`);
        this.currentMode = OperatorMode.DEV;
        break;
    }

    console.log(`MUTS starting in ${OPERATOR_MODE_CONFIGS[this.currentMode].displayName}`);
  }

  public static getInstance(): OperatorModeService {
    if (!OperatorModeService.instance) {
      OperatorModeService.instance = new OperatorModeService();
    }
    return OperatorModeService.instance;
  }

  public getCurrentMode(): OperatorMode {
    return this.currentMode;
  }

  public getModeConfig() {
    return OPERATOR_MODE_CONFIGS[this.currentMode];
  }

  public getRequirements(): OperatorModeRequirements {
    const config = this.getModeConfig();
    return {
      canWriteToEcu: config.allowsEcuWrites,
      canUseMockInterface: config.allowsMockInterface,
      needsRealHardware: config.requiresRealHardware,
      needsConfirmation: config.requiresConfirmation,
    };
  }

  // Permission checks
  public canWriteToEcu(): boolean {
    return this.getRequirements().canWriteToEcu;
  }

  public canUseMockInterface(): boolean {
    return this.getRequirements().canUseMockInterface;
  }

  public requiresRealHardware(): boolean {
    return this.getRequirements().needsRealHardware;
  }

  public requiresConfirmation(): boolean {
    return this.getRequirements().needsConfirmation;
  }

  // Validation helpers
  public validateEcuWrite(operation: string): { allowed: boolean; reason?: string } {
    if (!this.canWriteToEcu()) {
      return {
        allowed: false,
        reason: `ECU writes not allowed in ${OPERATOR_MODE_CONFIGS[this.currentMode].displayName}`,
      };
    }
    return { allowed: true };
  }

  public validateMockInterface(): { allowed: boolean; reason?: string } {
    if (!this.canUseMockInterface()) {
      return {
        allowed: false,
        reason: `Mock interface not available in ${OPERATOR_MODE_CONFIGS[this.currentMode].displayName}`,
      };
    }
    return { allowed: true };
  }

  public validateHardwareConnection(): { allowed: boolean; reason?: string } {
    if (this.requiresRealHardware() && this.currentMode === OperatorMode.DEV) {
      return {
        allowed: false,
        reason: `Real hardware required for ${OPERATOR_MODE_CONFIGS[this.currentMode].displayName}`,
      };
    }
    return { allowed: true };
  }
}

// Export singleton instance
export const operatorMode = OperatorModeService.getInstance();
