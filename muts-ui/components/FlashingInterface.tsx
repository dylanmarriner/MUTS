'use client';

import React, { useState, useEffect } from 'react';
import { flashAPI, ecuAPI } from '@/lib/api';
import { useHardware } from '@/contexts/HardwareContext';
import { 
  Zap, 
  Upload, 
  Download, 
  RotateCcw, 
  CheckCircle, 
  AlertTriangle, 
  Clock,
  FileText,
  Shield,
  Progress,
  Play,
  Square
} from 'lucide-react';

interface FlashSession {
  id: string;
  ecuId: string;
  fileName: string;
  fileHash: string;
  status: 'preparing' | 'flashing' | 'verifying' | 'completed' | 'failed' | 'rollback';
  progress: number;
  startTime: string;
  endTime?: string;
  checksumValidated: boolean;
  rollbackAvailable: boolean;
  ECU: {
    id: string;
    vin?: string;
    ecuType: string;
    firmwareVersion?: string;
  };
}

export default function FlashingInterface() {
  const [sessions, setSessions] = useState<FlashSession[]>([]);
  const [selectedSession, setSelectedSession] = useState<FlashSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [isFlashing, setIsFlashing] = useState(false);
  const { ecu } = useHardware();

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      setLoading(true);
      const response = await flashAPI.getSessions();
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

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    const validTypes = ['.bin', '.hex', '.s19'];
    const fileExt = file.name.substring(file.name.lastIndexOf('.'));
    if (!validTypes.includes(fileExt)) {
      alert(`Invalid file type. Supported: ${validTypes.join(', ')}`);
      return;
    }

    // Calculate hash (simplified - in real app would use crypto API)
    const hash = await calculateFileHash(file);
    
    try {
      const response = await flashAPI.createSession({
        ecuId: ecu.activeECU!,
        fileName: file.name,
        fileHash: hash
      });
      
      setUploadFile(file);
      await loadSessions();
      setSelectedSession(response.data);
    } catch (error) {
      console.error('Failed to create flash session:', error);
    }
  };

  const calculateFileHash = async (file: File): Promise<string> => {
    // Simplified hash calculation - would use SHA-256 in production
    return 'a'.repeat(64); // Placeholder
  };

  const startFlashing = async (sessionId: string) => {
    try {
      setIsFlashing(true);
      await flashAPI.startFlashing(sessionId);
      
      // Poll for progress
      const pollInterval = setInterval(async () => {
        const response = await flashAPI.getSession(sessionId);
        const session = response.data;
        
        // Update session in list
        setSessions(prev => prev.map(s => s.id === sessionId ? session : s));
        
        if (session.status === 'completed' || session.status === 'failed') {
          clearInterval(pollInterval);
          setIsFlashing(false);
          if (selectedSession?.id === sessionId) {
            setSelectedSession(session);
          }
        }
      }, 1000);
    } catch (error) {
      console.error('Failed to start flashing:', error);
      setIsFlashing(false);
    }
  };

  const createRollbackPoint = async (sessionId: string) => {
    try {
      await flashAPI.createRollbackPoint(sessionId);
      await loadSessions();
    } catch (error) {
      console.error('Failed to create rollback point:', error);
    }
  };

  const executeRollback = async (sessionId: string) => {
    if (!confirm('Are you sure you want to rollback to the previous firmware?')) {
      return;
    }

    try {
      await flashAPI.executeRollback(sessionId);
      await loadSessions();
    } catch (error) {
      console.error('Failed to execute rollback:', error);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'preparing':
        return <Clock className="w-4 h-4 text-workshop-500" />;
      case 'flashing':
        return <Zap className="w-4 h-4 text-mazda-500 animate-pulse" />;
      case 'verifying':
        return <Shield className="w-4 h-4 text-status-warning" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-status-ok" />;
      case 'failed':
        return <AlertTriangle className="w-4 h-4 text-status-error" />;
      case 'rollback':
        return <RotateCcw className="w-4 h-4 text-workshop-500" />;
      default:
        return <Clock className="w-4 h-4 text-workshop-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'preparing':
        return 'text-workshop-500';
      case 'flashing':
        return 'text-mazda-500';
      case 'verifying':
        return 'text-status-warning';
      case 'completed':
        return 'text-status-ok';
      case 'failed':
        return 'text-status-error';
      case 'rollback':
        return 'text-workshop-500';
      default:
        return 'text-workshop-500';
    }
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-workshop-100">ECU Flashing</h1>
          <p className="text-workshop-500 mt-1">
            Flash ECU firmware with rollback protection
          </p>
        </div>
        <label className="btn-primary cursor-pointer">
          <Upload className="w-4 h-4 mr-2" />
          Upload Firmware
          <input
            type="file"
            onChange={handleFileUpload}
            accept=".bin,.hex,.s19"
            className="hidden"
            disabled={!ecu.connected}
          />
        </label>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload Panel */}
        <div className="lg:col-span-1">
          <div className="card">
            <h2 className="text-lg font-semibold text-workshop-100 mb-4">Upload Firmware</h2>
            
            {!ecu.connected ? (
              <div className="text-center py-8">
                <AlertTriangle className="w-8 h-8 text-workshop-600 mx-auto mb-2" />
                <p className="text-workshop-500">Connect an ECU first</p>
              </div>
            ) : (
              <div className="space-y-4">
                {/* File Upload Area */}
                <div className="border-2 border-dashed border-workshop-700 rounded-lg p-6 text-center">
                  <Upload className="w-8 h-8 text-workshop-500 mx-auto mb-2" />
                  <p className="text-workshop-400 text-sm mb-2">
                    Drop firmware file here or click to browse
                  </p>
                  <p className="text-workshop-600 text-xs">
                    Supported: .bin, .hex, .s19 (Max 10MB)
                  </p>
                </div>

                {/* Uploaded File Info */}
                {uploadFile && (
                  <div className="bg-workshop-800 rounded-lg p-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-workshop-400" />
                        <span className="text-sm text-workshop-100 truncate">
                          {uploadFile.name}
                        </span>
                      </div>
                      <span className="text-xs text-workshop-500">
                        {(uploadFile.size / 1024 / 1024).toFixed(2)} MB
                      </span>
                    </div>
                  </div>
                )}

                {/* Supported ECUs */}
                <div className="text-sm">
                  <p className="text-workshop-500 mb-2">Supported ECUs:</p>
                  <ul className="space-y-1 text-workshop-400">
                    <li>• MazdaSpeed3 (ISO-TP, UDS)</li>
                    <li>• Mazda6 (ISO-TP, KWP2000)</li>
                    <li>• CX-5 (CAN, UDS)</li>
                  </ul>
                </div>
              </div>
            )}
          </div>

          {/* Flashing Guide */}
          <div className="card mt-4">
            <h3 className="text-sm font-semibold text-workshop-100 mb-3">Flashing Process</h3>
            <div className="space-y-2 text-xs text-workshop-400">
              <div className="flex items-start gap-2">
                <span className="text-mazda-500">1.</span>
                <span>Upload firmware file</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-mazda-500">2.</span>
                <span>Create rollback point</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-mazda-500">3.</span>
                <span>Start flashing process</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-mazda-500">4.</span>
                <span>Verify checksum</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-mazda-500">5.</span>
                <span>Rollback if needed</span>
              </div>
            </div>
          </div>
        </div>

        {/* Sessions List */}
        <div className="lg:col-span-2">
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-workshop-100">Flash Sessions</h2>
              <button onClick={loadSessions} className="btn-ghost text-sm">
                <RotateCcw className="w-4 h-4 mr-1" />
                Refresh
              </button>
            </div>

            {loading ? (
              <div className="flex items-center justify-center h-32">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-mazda-500"></div>
              </div>
            ) : sessions.length === 0 ? (
              <div className="text-center py-8">
                <Zap className="w-8 h-8 text-workshop-600 mx-auto mb-2" />
                <p className="text-workshop-500">No flash sessions yet</p>
                <p className="text-workshop-600 text-sm mt-1">
                  Upload a firmware file to get started
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {sessions.map((session) => (
                  <div
                    key={session.id}
                    className="p-4 border border-workshop-800 rounded-lg hover:border-workshop-700 transition-colors"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        {getStatusIcon(session.status)}
                        <div>
                          <div className="font-medium text-workshop-100">
                            {session.fileName}
                          </div>
                          <div className="text-sm text-workshop-500">
                            {session.ECU.ecuType} • {new Date(session.startTime).toLocaleString()}
                          </div>
                        </div>
                      </div>
                      <div className={`text-sm font-medium ${getStatusColor(session.status)}`}>
                        {session.status.toUpperCase()}
                      </div>
                    </div>

                    {/* Progress Bar */}
                    {(session.status === 'flashing' || session.status === 'verifying') && (
                      <div className="mb-3">
                        <div className="flex items-center justify-between text-sm mb-1">
                          <span className="text-workshop-400">Progress</span>
                          <span className="text-workshop-300">{session.progress.toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-workshop-800 rounded-full h-2">
                          <div
                            className="bg-mazda-500 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${session.progress}%` }}
                          ></div>
                        </div>
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex items-center gap-2">
                      {session.status === 'preparing' && (
                        <>
                          <button
                            onClick={() => createRollbackPoint(session.id)}
                            className="btn-secondary text-sm"
                          >
                            <Shield className="w-4 h-4 mr-1" />
                            Create Rollback
                          </button>
                          <button
                            onClick={() => startFlashing(session.id)}
                            disabled={isFlashing}
                            className="btn-primary text-sm disabled:opacity-50"
                          >
                            <Play className="w-4 h-4 mr-1" />
                            Start Flash
                          </button>
                        </>
                      )}
                      
                      {session.status === 'completed' && (
                        <>
                          {!session.checksumValidated && (
                            <button className="btn-secondary text-sm">
                              <CheckCircle className="w-4 h-4 mr-1" />
                              Verify
                            </button>
                          )}
                          {session.rollbackAvailable && (
                            <button
                              onClick={() => executeRollback(session.id)}
                              className="btn-ghost text-sm text-status-error"
                            >
                              <RotateCcw className="w-4 h-4 mr-1" />
                              Rollback
                            </button>
                          )}
                        </>
                      )}

                      <button className="btn-ghost text-sm">
                        <Download className="w-4 h-4 mr-1" />
                        Export Log
                      </button>
                    </div>

                    {/* Status Details */}
                    <div className="mt-3 pt-3 border-t border-workshop-800 flex gap-4 text-xs text-workshop-500">
                      <span>Hash: {session.fileHash.substring(0, 8)}...</span>
                      {session.checksumValidated && (
                        <span className="text-status-ok">✓ Verified</span>
                      )}
                      {session.rollbackAvailable && (
                        <span className="text-status-warning">Rollback Available</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}