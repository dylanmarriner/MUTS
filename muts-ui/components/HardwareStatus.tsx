'use client';

import React from 'react';
import { useHardware } from '@/contexts/HardwareContext';
import { 
  Wifi, 
  WifiOff, 
  Cpu, 
  AlertCircle, 
  CheckCircle, 
  Activity,
  RefreshCw
} from 'lucide-react';

export default function HardwareStatus() {
  const { hardware, ecu, agents, refreshHardware, refreshECU, isPolling } = useHardware();

  return (
    <div className="bg-workshop-900 border-b border-workshop-800 px-6 py-3">
      <div className="flex items-center justify-between">
        {/* Left side - Hardware Status */}
        <div className="flex items-center gap-6">
          {/* Backend Connection */}
          <div className="flex items-center gap-2">
            {hardware.connected ? (
              <>
                <CheckCircle className="w-4 h-4 text-status-ok" />
                <span className="text-sm text-workshop-300">Backend Connected</span>
              </>
            ) : (
              <>
                <AlertCircle className="w-4 h-4 text-status-error" />
                <span className="text-sm text-workshop-400">Backend Offline</span>
              </>
            )}
          </div>

          {/* ECU Connection */}
          <div className="flex items-center gap-2">
            {ecu.connected ? (
              <>
                <Cpu className="w-4 h-4 text-status-ok" />
                <span className="text-sm text-workshop-300">
                  ECU: {ecu.vin} ({ecu.protocol})
                </span>
              </>
            ) : (
              <>
                <WifiOff className="w-4 h-4 text-status-offline" />
                <span className="text-sm text-workshop-400">No ECU Connected</span>
              </>
            )}
          </div>

          {/* Device Info */}
          {hardware.device && (
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-workshop-500" />
              <span className="text-sm text-workshop-400">
                {hardware.device} - {hardware.deviceType}
              </span>
            </div>
          )}
        </div>

        {/* Right side - Agent Status & Controls */}
        <div className="flex items-center gap-6">
          {/* Agent Status */}
          <div className="flex items-center gap-4">
            <div className="text-sm">
              <span className="text-workshop-500">Agents:</span>
              <span className="ml-2 text-workshop-300">{agents.running} running</span>
              <span className="ml-2 text-workshop-500">/ {agents.totalAgents} total</span>
            </div>
            
            {agents.error > 0 && (
              <div className="flex items-center gap-1">
                <AlertCircle className="w-4 h-4 text-status-error" />
                <span className="text-sm text-status-error">{agents.error} errors</span>
              </div>
            )}
          </div>

          {/* Refresh Button */}
          <button
            onClick={() => {
              refreshHardware();
              refreshECU();
            }}
            disabled={isPolling}
            className="btn-ghost p-2"
            title="Refresh hardware status"
          >
            <RefreshCw className={`w-4 h-4 ${isPolling ? 'animate-spin' : ''}`} />
          </button>

          {/* Polling Indicator */}
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isPolling ? 'bg-status-ok animate-pulse' : 'bg-status-offline'}`} />
            <span className="text-xs text-workshop-500">
              {isPolling ? 'Auto-refresh' : 'Manual'}
            </span>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {hardware.error && (
        <div className="mt-3 flex items-center gap-2 text-status-error text-sm">
          <AlertCircle className="w-4 h-4" />
          <span>{hardware.error}</span>
        </div>
      )}
    </div>
  );
}