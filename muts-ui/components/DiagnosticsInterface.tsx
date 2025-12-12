'use client';

import React, { useState, useEffect } from 'react';
import { diagnosticsAPI, ecuAPI } from '@/lib/api';
import { useHardware } from '@/contexts/HardwareContext';
import { 
  Play, 
  Square, 
  Download, 
  AlertTriangle, 
  CheckCircle, 
  Info,
  Activity,
  Zap,
  Eye,
  Trash2
} from 'lucide-react';

interface DiagnosticSession {
  id: string;
  ecuId: string;
  startTime: string;
  endTime?: string;
  status: 'running' | 'completed' | 'error';
  ECU: {
    id: string;
    vin?: string;
    ecuType: string;
  };
  _count: {
    dtcs: number;
    freezeFrames: number;
    liveData: number;
  };
  dtcs: Array<{
    code: string;
    description: string;
    severity: 'info' | 'warning' | 'error' | 'critical';
    status: 'active' | 'stored' | 'pending';
  }>;
}

export default function DiagnosticsInterface() {
  const [sessions, setSessions] = useState<DiagnosticSession[]>([]);
  const [selectedSession, setSelectedSession] = useState<DiagnosticSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [ecus, setECUs] = useState<any[]>([]);
  const { ecu } = useHardware();

  useEffect(() => {
    loadSessions();
    loadECUs();
  }, []);

  const loadSessions = async () => {
    try {
      setLoading(true);
      const response = await diagnosticsAPI.getSessions();
      setSessions(response.data);
      if (response.data.length > 0 && !selectedSession) {
        setSelectedSession(response.data[0]);
      }
    } catch (error) {
      console.error('Failed to load sessions:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadECUs = async () => {
    try {
      const response = await ecuAPI.getAll();
      setECUs(response.data);
    } catch (error) {
      console.error('Failed to load ECUs:', error);
    }
  };

  const startNewSession = async () => {
    if (!ecu.connected) {
      alert('No ECU connected');
      return;
    }

    try {
      const response = await diagnosticsAPI.createSession({
        ecuId: ecu.activeECU!,
        status: 'running'
      });
      await loadSessions();
      setSelectedSession(response.data);
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  const runFullScan = async (sessionId: string) => {
    try {
      await diagnosticsAPI.runFullScan(sessionId);
      // In real app, would poll for updates
      await loadSessions();
    } catch (error) {
      console.error('Failed to run scan:', error);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Activity className="w-4 h-4 text-mazda-500 animate-pulse" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-status-ok" />;
      case 'error':
        return <AlertTriangle className="w-4 h-4 text-status-error" />;
      default:
        return <Info className="w-4 h-4 text-workshop-500" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'text-status-error bg-status-error/20';
      case 'error':
        return 'text-status-error bg-status-error/10';
      case 'warning':
        return 'text-status-warning bg-status-warning/10';
      default:
        return 'text-workshop-400 bg-workshop-800/50';
    }
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-workshop-100">Diagnostics</h1>
          <p className="text-workshop-500 mt-1">
            Scan and analyze ECU for issues and performance data
          </p>
        </div>
        <button 
          onClick={startNewSession}
          disabled={!ecu.connected}
          className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Play className="w-4 h-4 mr-2" />
          New Session
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sessions List */}
        <div className="lg:col-span-1">
          <div className="card">
            <h2 className="text-lg font-semibold text-workshop-100 mb-4">Sessions</h2>
            
            {loading ? (
              <div className="flex items-center justify-center h-32">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-mazda-500"></div>
              </div>
            ) : sessions.length === 0 ? (
              <div className="text-center py-8">
                <Activity className="w-8 h-8 text-workshop-600 mx-auto mb-2" />
                <p className="text-workshop-500">No sessions yet</p>
                <button onClick={startNewSession} className="btn-ghost mt-2 text-sm">
                  Create first session
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                {sessions.map((session) => (
                  <div
                    key={session.id}
                    onClick={() => setSelectedSession(session)}
                    className={`p-3 rounded-lg border cursor-pointer transition-all ${
                      selectedSession?.id === session.id
                        ? 'border-mazda-500 bg-workshop-800'
                        : 'border-workshop-700 hover:border-workshop-600'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(session.status)}
                        <span className="text-sm font-medium text-workshop-100">
                          {session.ECU.ecuType}
                        </span>
                      </div>
                      <span className="text-xs text-workshop-500">
                        {new Date(session.startTime).toLocaleTimeString()}
                      </span>
                    </div>
                    <div className="text-xs text-workshop-400">
                      {session.ECU.vin || 'No VIN'}
                    </div>
                    <div className="flex gap-4 mt-2 text-xs">
                      <span className="text-workshop-500">
                        DTCs: <span className="text-workshop-300">{session._count.dtcs}</span>
                      </span>
                      <span className="text-workshop-500">
                        Data: <span className="text-workshop-300">{session._count.liveData}</span>
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Session Details */}
        <div className="lg:col-span-2">
          {selectedSession ? (
            <div className="space-y-6">
              {/* Session Info */}
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-workshop-100">
                    Session Details
                  </h2>
                  <div className="flex items-center gap-2">
                    {selectedSession.status === 'running' && (
                      <button
                        onClick={() => runFullScan(selectedSession.id)}
                        className="btn-secondary text-sm"
                      >
                        <Zap className="w-4 h-4 mr-1" />
                        Full Scan
                      </button>
                    )}
                    <button className="btn-ghost text-sm">
                      <Download className="w-4 h-4 mr-1" />
                      Export
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-workshop-500">ECU:</span>
                    <p className="text-workshop-100 font-medium">{selectedSession.ECU.ecuType}</p>
                  </div>
                  <div>
                    <span className="text-workshop-500">VIN:</span>
                    <p className="text-workshop-100 font-mono">{selectedSession.ECU.vin || 'Unknown'}</p>
                  </div>
                  <div>
                    <span className="text-workshop-500">Started:</span>
                    <p className="text-workshop-100">
                      {new Date(selectedSession.startTime).toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <span className="text-workshop-500">Status:</span>
                    <div className="flex items-center gap-2 mt-1">
                      {getStatusIcon(selectedSession.status)}
                      <span className="text-workshop-100 capitalize">{selectedSession.status}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* DTCs */}
              <div className="card">
                <h3 className="text-lg font-semibold text-workshop-100 mb-4">
                  Diagnostic Trouble Codes
                </h3>
                
                {selectedSession.dtcs.length === 0 ? (
                  <div className="text-center py-8">
                    <CheckCircle className="w-8 h-8 text-status-ok mx-auto mb-2" />
                    <p className="text-workshop-500">No DTCs detected</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {selectedSession.dtcs.map((dtc, index) => (
                      <div
                        key={index}
                        className={`p-3 rounded-lg border ${getSeverityColor(dtc.severity)}`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <span className="font-mono font-bold">{dtc.code}</span>
                            <span className="text-sm">{dtc.description}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs px-2 py-1 rounded bg-workshop-800/50">
                              {dtc.status}
                            </span>
                            <button className="btn-ghost p-1" title="View details">
                              <Eye className="w-4 h-4" />
                            </button>
                            <button className="btn-ghost p-1 text-status-error" title="Clear">
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Live Data Preview */}
              {selectedSession._count.liveData > 0 && (
                <div className="card">
                  <h3 className="text-lg font-semibold text-workshop-100 mb-4">
                    Live Data Preview
                  </h3>
                  <div className="diagnostic-grid">
                    <div className="metric-card">
                      <div className="metric-value">2,450</div>
                      <div className="metric-label">Engine RPM</div>
                    </div>
                    <div className="metric-card">
                      <div className="metric-value">85°C</div>
                      <div className="metric-label">Coolant Temp</div>
                    </div>
                    <div className="metric-card">
                      <div className="metric-value">14.7</div>
                      <div className="metric-label">AFR</div>
                    </div>
                    <div className="metric-card">
                      <div className="metric-value">101 kPa</div>
                      <div className="metric-label">MAP</div>
                    </div>
                    <div className="metric-card">
                      <div className="metric-value">15°</div>
                      <div className="metric-label">Ignition Timing</div>
                    </div>
                    <div className="metric-card">
                      <div className="metric-value">0%</div>
                      <div className="metric-label">Throttle</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="card text-center py-12">
              <Activity className="w-12 h-12 text-workshop-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-workshop-100 mb-2">
                No Session Selected
              </h3>
              <p className="text-workshop-500">
                Select a session from the list or create a new one to begin diagnostics
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}