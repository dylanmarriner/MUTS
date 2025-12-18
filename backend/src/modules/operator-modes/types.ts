/**
 * Operator Modes Configuration
 * Defines the three runtime modes for MUTS
 */

export enum OperatorMode {
  DEV = 'dev',
  WORKSHOP = 'workshop',
  LAB = 'lab',
}

export interface OperatorModeConfig {
  mode: OperatorMode;
  allowsMockInterface: boolean;
  allowsEcuWrites: boolean;
  requiresRealHardware: boolean;
  requiresConfirmation: boolean;
  displayName: string;
  description: string;
  color: 'blue' | 'green' | 'red';
}

export const OPERATOR_MODE_CONFIGS: Record<OperatorMode, OperatorModeConfig> = {
  [OperatorMode.DEV]: {
    mode: OperatorMode.DEV,
    allowsMockInterface: true,
    allowsEcuWrites: false,
    requiresRealHardware: false,
    requiresConfirmation: false,
    displayName: 'DEV MODE',
    description: 'Development mode with mock interface',
    color: 'blue',
  },
  [OperatorMode.WORKSHOP]: {
    mode: OperatorMode.WORKSHOP,
    allowsMockInterface: false,
    allowsEcuWrites: true,
    requiresRealHardware: true,
    requiresConfirmation: true,
    displayName: 'WORKSHOP MODE',
    description: 'Workshop mode for real vehicle servicing',
    color: 'green',
  },
  [OperatorMode.LAB]: {
    mode: OperatorMode.LAB,
    allowsMockInterface: false,
    allowsEcuWrites: true,
    requiresRealHardware: true,
    requiresConfirmation: true,
    displayName: 'LAB MODE (DANGEROUS)',
    description: 'Research mode with expanded capabilities',
    color: 'red',
  },
};

export interface OperatorModeRequirements {
  canWriteToEcu: boolean;
  canUseMockInterface: boolean;
  needsRealHardware: boolean;
  needsConfirmation: boolean;
}
