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
    <div className="bg-bg-glass backdrop-blur-holo border-b border-cyan-500/30 px-6 py-3 noise">
      <div className="flex items-center justify-between">
        {/* Left side - Hardware Status */}
        <div className="flex items-center gap-6">
          {/* Backend Connection */}
          <div className="flex items-center gap-2">
            {hardware.connected ? (
              <>
                <CheckCircle className="w-4 h-4 text-green-400" />
                <span className="text-sm text-cyan-400 font-mono">Backend Connected</span>
              </>
            ) : (
              <>
                <AlertCircle className="w-4 h-4 text-red-400" />
                <span className="text-sm text-text-tertiary font-mono">Backend Offline</span>
              </>
            )}
          </div>

          {/* ECU Connection */}
          <div className="flex items-center gap-2">
            {ecu.connected ? (
              <>
                <Cpu className="w-4 h-4 text-green-400" />
                <span className="text-sm text-cyan-400 font-mono">
                  ECU: {ecu.vin} ({ecu.protocol})
                </span>
              </>
            ) : (
              <>
                <WifiOff className="w-4 h-4 text-text-muted" />
                <span className="text-sm text-text-tertiary font-mono">No ECU Connected</span>
              </>
            )}
          </div>

          {/* Device Info */}
          {hardware.device && (
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-violet-400" />
              <span className="text-sm text-text-secondary font-mono">
                {hardware.device} - {hardware.deviceType}
              </span>
            </div>
          )}
        </div>

        {/* Right side - Agent Status & Controls */}
        <div className="flex items-center gap-6">
          {/* Agent Status */}
          <div className="flex items-center gap-4">
            <div className="text-sm font-mono">
              <span className="text-text-muted">Agents:</span>
              <span className="ml-2 text-cyan-400">{agents.running} running</span>
              <span className="ml-2 text-text-muted">/ {agents.totalAgents} total</span>
            </div>
            
            {agents.error > 0 && (
              <div className="flex items-center gap-1">
                <AlertCircle className="w-4 h-4 text-red-400" />
                <span className="text-sm text-red-400 font-mono">{agents.error} errors</span>
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
            className="btn-ghost p-2 text-cyan-400 hover:text-cyan-300 hover:bg-cyan-600/10"
            title="Refresh hardware status"
          >
            <RefreshCw className={`w-4 h-4 ${isPolling ? 'animate-spin' : ''}`} />
          </button>

          {/* Polling Indicator */}
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isPolling ? 'bg-green-400 animate-pulse' : 'bg-text-muted'}`} />
            <span className="text-xs text-text-muted font-mono">
              {isPolling ? 'Auto-refresh' : 'Manual'}
            </span>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {hardware.error && (
        <div className="mt-3 flex items-center gap-2 text-red-400 text-sm font-mono">
          <AlertCircle className="w-4 h-4" />
          <span>{hardware.error}</span>
        </div>
      )}
    </div>
  );
}