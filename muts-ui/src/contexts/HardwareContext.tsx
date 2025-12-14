'use client';

import React, { createContext, useContext, useState, useEffect, useRef, ReactNode } from 'react';
import { agentAPI, ecuAPI, healthAPI } from '@/lib/api';

interface HardwareStatus {
  connected: boolean;
  device: string | null;
  deviceType: string | null;
  lastUpdate: Date | null;
  error: string | null;
}

interface ECUStatus {
  connected: boolean;
  activeECU: string | null;
  vin: string | null;
  protocol: string | null;
  lastUpdate: Date | null;
}

interface AgentStatus {
  totalAgents: number;
  running: number;
  idle: number;
  error: number;
  completed: number;
}

interface HardwareContextType {
  hardware: HardwareStatus;
  ecu: ECUStatus;
  agents: AgentStatus;
  isPolling: boolean;
  refreshHardware: () => Promise<void>;
  refreshECU: () => Promise<void>;
  refreshAgents: () => Promise<void>;
  startPolling: () => void;
  stopPolling: () => void;
}

const HardwareContext = createContext<HardwareContextType | undefined>(undefined);

export function HardwareProvider({ children }: { children: ReactNode }) {
  const [hardware, setHardware] = useState<HardwareStatus>({
    connected: false,
    device: null,
    deviceType: null,
    lastUpdate: null,
    error: null,
  });

  const [ecu, setECU] = useState<ECUStatus>({
    connected: false,
    activeECU: null,
    vin: null,
    protocol: null,
    lastUpdate: null,
  });

  const [agents, setAgents] = useState<AgentStatus>({
    totalAgents: 0,
    running: 0,
    idle: 0,
    error: 0,
    completed: 0,
  });

  const [isPolling, setIsPolling] = useState(false);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const refreshHardware = async () => {
    try {
      const response = await healthAPI.check();
      if (response.status === 200) {
        setHardware({
          connected: true,
          device: 'J2534 Interface',
          deviceType: 'Diagnostic Tool',
          lastUpdate: new Date(),
          error: null,
        });
      }
    } catch (error) {
      setHardware({
        connected: false,
        device: null,
        deviceType: null,
        lastUpdate: new Date(),
        error: 'Unable to connect to backend',
      });
    }
  };

  const refreshECU = async () => {
    try {
      const ecus = await ecuAPI.getAll();
      if (ecus.data.length > 0) {
        const activeECU = ecus.data[0]; // For now, take the first ECU
        setECU({
          connected: true,
          activeECU: activeECU.id,
          vin: activeECU.vin || 'Unknown',
          protocol: activeECU.protocol,
          lastUpdate: new Date(),
        });
      } else {
        setECU({
          connected: false,
          activeECU: null,
          vin: null,
          protocol: null,
          lastUpdate: new Date(),
        });
      }
    } catch (error) {
      setECU({
        connected: false,
        activeECU: null,
        vin: null,
        protocol: null,
        lastUpdate: new Date(),
      });
    }
  };

  const refreshAgents = async () => {
    try {
      const response = await agentAPI.getCoordinationStatus();
      setAgents(response.data);
    } catch (error) {
      console.error('Failed to fetch agent status:', error);
    }
  };

  const startPolling = () => {
    if (isPolling) return;
    
    setIsPolling(true);
    
    // Initial refresh
    refreshHardware();
    refreshECU();
    refreshAgents();
    
    // Set up polling
    pollIntervalRef.current = setInterval(() => {
      refreshHardware();
      refreshECU();
      refreshAgents();
    }, 5000); // Poll every 5 seconds
  };

  const stopPolling = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    setIsPolling(false);
  };

  useEffect(() => {
    // Start polling when provider mounts
    startPolling();
    
    // Cleanup on unmount
    return () => {
      stopPolling();
    };
  }, []);

  const value: HardwareContextType = {
    hardware,
    ecu,
    agents,
    isPolling,
    refreshHardware,
    refreshECU,
    refreshAgents,
    startPolling,
    stopPolling,
  };

  return (
    <HardwareContext.Provider value={value}>
      {children}
    </HardwareContext.Provider>
  );
}

export function useHardware() {
  const context = useContext(HardwareContext);
  if (context === undefined) {
    throw new Error('useHardware must be used within a HardwareProvider');
  }
  return context;
}