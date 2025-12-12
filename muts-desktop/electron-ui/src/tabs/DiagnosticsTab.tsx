/**
 * Diagnostics Tab
 * DTC reading, clearing, and diagnostic procedures
 */

import React, { useEffect, useState } from 'react';
import { Wrench, AlertTriangle, CheckCircle, XCircle, Play } from 'lucide-react';
import { useConnectionState, useAppStore } from '../stores/useAppStore';

interface DTCInfo {
  code: string;
  description: string;
  status: 'active' | 'stored' | 'pending';
  timestamp: Date;
  freezeFrame?: Record<string, number>;
}

const DiagnosticsTab: React.FC = () => {
  const { isConnected, isDisconnected, currentSession } = useConnectionState();
  const [dtcs, setDtcs] = useState<DTCInfo[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [diagnosticSession, setDiagnosticSession] = useState<string | null>(null);

  useEffect(() => {
    if (isConnected) {
      loadDTCs();
    }
  }, [isConnected]);

  const loadDTCs = async () => {
    try {
      const dtcList = await window.electronAPI.diagnostic.readDTCs();
      setDtcs(dtcList.map((dtc: any) => ({
        ...dtc,
        timestamp: new Date(dtc.timestamp),
      })));
    } catch (error) {
      console.error('Failed to load DTCs:', error);
    }
  };

  const startDiagnosticSession = async () => {
    if (!currentSession) return;
    
    setIsRunning(true);
    try {
      const sessionId = await window.electronAPI.diagnostic.start();
      setDiagnosticSession(sessionId);
    } catch (error) {
      console.error('Failed to start diagnostic session:', error);
    } finally {
      setIsRunning(false);
    }
  };

  const clearDTCs = async () => {
    if (!currentSession) return;
    
    try {
      await window.electronAPI.diagnostic.clearDTCs(currentSession.id);
      setDtcs([]);
    } catch (error) {
      console.error('Failed to clear DTCs:', error);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <XCircle className="text-red-500" size={16} />;
      case 'stored':
        return <AlertTriangle className="text-yellow-500" size={16} />;
      case 'pending':
        return <Play className="text-blue-500" size={16} />;
      default:
        return <CheckCircle className="text-green-500" size={16} />;
    }
  };

  if (isDisconnected) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <Wrench size={64} className="mx-auto text-gray-600 mb-4" />
          <h2 className="text-xl font-semibold text-gray-400 mb-2">NO_INTERFACE_CONNECTED</h2>
          <p className="text-gray-500">Connect to an interface to perform diagnostics</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 p-6 overflow-auto">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
          <Wrench size={24} />
          Diagnostics
        </h1>

        {/* Diagnostic Controls */}
        <div className="bg-gray-900 rounded-lg p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Diagnostic Session</h2>
          <div className="flex items-center gap-4">
            <button
              onClick={startDiagnosticSession}
              disabled={isRunning}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 rounded-lg transition-colors flex items-center gap-2"
            >
              <Play size={16} />
              {isRunning ? 'Starting...' : 'Start Session'}
            </button>
            
            <button
              onClick={clearDTCs}
              disabled={!currentSession || dtcs.length === 0}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-700 rounded-lg transition-colors"
            >
              Clear DTCs
            </button>
            
            {diagnosticSession && (
              <span className="text-sm text-gray-400">
                Session: {diagnosticSession.substring(0, 8)}
              </span>
            )}
          </div>
        </div>

        {/* DTC List */}
        <div className="bg-gray-900 rounded-lg overflow-hidden">
          <div className="p-4 border-b border-gray-800">
            <h2 className="text-lg font-semibold">Diagnostic Trouble Codes</h2>
          </div>
          
          {dtcs.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <CheckCircle size={48} className="mx-auto mb-2 opacity-50" />
              <p>No DTCs detected</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-800">
              {dtcs.map((dtc, index) => (
                <div key={index} className="p-4 hover:bg-gray-800/50 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      {getStatusIcon(dtc.status)}
                      <div>
                        <div className="font-mono font-semibold text-lg">{dtc.code}</div>
                        <div className="text-gray-400 mt-1">{dtc.description}</div>
                        <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                          <span>Status: {dtc.status}</span>
                          <span>Detected: {dtc.timestamp.toLocaleString()}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {dtc.freezeFrame && (
                    <div className="mt-4 p-3 bg-gray-800 rounded-lg">
                      <div className="text-sm font-medium text-gray-400 mb-2">Freeze Frame Data</div>
                      <div className="grid grid-cols-3 gap-2 text-sm">
                        {Object.entries(dtc.freezeFrame).map(([key, value]) => (
                          <div key={key} className="flex justify-between">
                            <span className="text-gray-400">{key}:</span>
                            <span className="font-mono">{value}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick Tests */}
        <div className="mt-6 bg-gray-900 rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Quick Tests</h2>
          <div className="grid grid-cols-2 gap-4">
            <button className="p-4 bg-gray-800 hover:bg-gray-700 rounded-lg text-left transition-colors">
              <h3 className="font-medium mb-1">Read VIN</h3>
              <p className="text-sm text-gray-400">Read vehicle identification number</p>
            </button>
            
            <button className="p-4 bg-gray-800 hover:bg-gray-700 rounded-lg text-left transition-colors">
              <h3 className="font-medium mb-1">Read ECU Info</h3>
              <p className="text-sm text-gray-400">Read ECU identification data</p>
            </button>
            
            <button className="p-4 bg-gray-800 hover:bg-gray-700 rounded-lg text-left transition-colors">
              <h3 className="font-medium mb-1">System Test</h3>
              <p className="text-sm text-gray-400">Run comprehensive system test</p>
            </button>
            
            <button className="p-4 bg-gray-800 hover:bg-gray-700 rounded-lg text-left transition-colors">
              <h3 className="font-medium mb-1">Mode $06</h3>
              <p className="text-sm text-gray-400">On-board monitoring test results</p>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DiagnosticsTab;
