// Operator and technician types

export type OperatorMode = 'Workshop' | 'EndUser' | 'Developer' | 'Diagnostics';

export interface Technician {
  id: string;
  name: string;
  email?: string;
  role?: string;
  certifications?: string[];
}

export interface VehicleInfo {
  vin?: string;
  make?: string;
  model?: string;
  year?: number;
  ecuType?: string;
  calibrationId?: string;
}

export interface Config {
  operatorMode?: OperatorMode;
  technicianId?: string;
  requireModeSelection?: boolean;
  [key: string]: any;
}
