'use client';

import React, { useState, useEffect } from 'react';
import { securityAPI, ecuAPI } from '@/lib/api';
import { useHardware } from '@/contexts/HardwareContext';
import { 
  Shield, 
  Key, 
  Lock, 
  Unlock, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  Eye,
  EyeOff,
  Copy,
  RefreshCw
} from 'lucide-react';

interface SecuritySession {
  id: string;
  ecuId: string;
  level: string;
  seed?: string;
  key?: string;
  algorithm?: string;
  success: boolean;
  createdAt: string;
  ECU: {
    id: string;
    vin?: string;
    ecuType: string;
    securityAlgorithm?: string;
  };
}

export default function SecurityInterface() {
  const [sessions, setSessions] = useState<SecuritySession[]>([]);
  const [selectedSession, setSelectedSession] = useState<SecuritySession | null>(null);
  const [loading, setLoading] = useState(true);
  const [accessLevel, setAccessLevel] = useState('LEVEL_1');
  const [seed, setSeed] = useState('');
  const [key, setKey] = useState('');
  const [showSeed, setShowSeed] = useState(false);
  const [showKey, setShowKey] = useState(false);
  const [isManufacturerMode, setIsManufacturerMode] = useState(false);
  const { ecu } = useHardware();

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      setLoading(true);
      const response = await securityAPI.getSessions();
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

  const requestAccess = async () => {
    if (!ecu.connected) {
      alert('No ECU connected');
      return;
    }

    try {
      const response = await securityAPI.requestAccess({
        ecuId: ecu.activeECU!,
        level: accessLevel
      });
      
      setSeed(response.data.seed);
      setSelectedSession(null);
      await loadSessions();
    } catch (error) {
      console.error('Failed to request access:', error);
    }
  };

  const submitKey = async () => {
    if (!selectedSession) return;

    try {
      const response = await securityAPI.submitKey(selectedSession.id, { key });
      
      if (response.data.success) {
        await loadSessions();
        setKey('');
        setSeed('');
      }
    } catch (error) {
      console.error('Failed to submit key:', error);
    }
  };

  const enterManufacturerMode = async () => {
    if (!ecu.connected) return;

    try {
      const response = await securityAPI.enterManufacturerMode({
        ecuId: ecu.activeECU!
      });
      
      if (response.data.success) {
        setIsManufacturerMode(true);
      }
    } catch (error) {
      console.error('Failed to enter manufacturer mode:', error);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-amber-400 font-mono glitch">Security</h1>
          <p className="text-violet-400 mt-1 font-mono text-sm">
            Manage ECU security access and authentication
          </p>
        </div>
        {isManufacturerMode && (
          <div className="flex items-center gap-2 px-3 py-1 bg-amber-500/20 border border-amber-500/50 rounded-lg shadow-glow-amber">
            <Shield className="w-4 h-4 text-amber-400" />
            <span className="text-sm text-amber-400 font-mono">Manufacturer Mode</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Access Request Panel */}
        <div className="lg:col-span-1">
          <div className="card-amber">
            <h2 className="text-lg font-semibold text-amber-400 font-mono mb-4">Request Access</h2>
            
            {!ecu.connected ? (
              <div className="text-center py-8">
                <Lock className="w-8 h-8 text-text-muted mx-auto mb-2" />
                <p className="text-text-tertiary font-mono">Connect an ECU first</p>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Access Level */}
                <div>
                  <label className="block text-sm font-medium text-amber-400 mb-2 font-mono">
                    Access Level
                  </label>
                  <select
                    value={accessLevel}
                    onChange={(e) => setAccessLevel(e.target.value)}
                    className="input w-full"
                  >
                    <option value="LEVEL_1">Level 1 - Basic Security</option>
                    <option value="LEVEL_2">Level 2 - Advanced Security</option>
                    <option value="MANUFACTURER">Manufacturer Mode</option>
                  </select>
                </div>

                {/* Request Button */}
                <button
                  onClick={requestAccess}
                  disabled={seed !== ''}
                  className="btn-secondary w-full disabled:opacity-50"
                >
                  <Key className="w-4 h-4 mr-2" />
                  Request Seed
                </button>

                {/* Seed Display */}
                {seed && (
                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-amber-400 font-mono">
                      Seed (Hex)
                    </label>
                    <div className="relative">
                      <input
                        type={showSeed ? 'text' : 'password'}
                        value={seed}
                        readOnly
                        className="input pr-20 w-full font-mono text-sm"
                      />
                      <div className="absolute right-1 top-1/2 transform -translate-y-1/2 flex gap-1">
                        <button
                          onClick={() => setShowSeed(!showSeed)}
                          className="btn-ghost p-1 text-amber-400 hover:text-amber-300"
                        >
                          {showSeed ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        </button>
                        <button
                          onClick={() => copyToClipboard(seed)}
                          className="btn-ghost p-1 text-amber-400 hover:text-amber-300"
                        >
                          <Copy className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* Key Input */}
                {seed && (
                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-workshop-300">
                      Key (Hex)
                    </label>
                    <div className="relative">
                      <input
                        type={showKey ? 'text' : 'password'}
                        value={key}
                        onChange={(e) => setKey(e.target.value)}
                        placeholder="Enter computed key"
                        className="input pr-10 w-full font-mono text-sm"
                      />
                      <button
                        onClick={() => setShowKey(!showKey)}
                        className="absolute right-1 top-1/2 transform -translate-y-1/2 btn-ghost p-1"
                      >
                        {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                )}

                {/* Submit Button */}
                {seed && (
                  <button
                    onClick={submitKey}
                    disabled={!key}
                    className="btn-primary w-full disabled:opacity-50"
                  >
                    <Unlock className="w-4 h-4 mr-2" />
                    Submit Key
                  </button>
                )}

                {/* Manufacturer Mode */}
                {accessLevel === 'MANUFACTURER' && !isManufacturerMode && (
                  <button
                    onClick={enterManufacturerMode}
                    className="btn-secondary w-full"
                  >
                    <Shield className="w-4 h-4 mr-2" />
                    Enter Manufacturer Mode
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Algorithm Info */}
          <div className="card mt-4">
            <h3 className="text-sm font-semibold text-workshop-100 mb-3">Supported Algorithms</h3>
            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-workshop-400">M12R v3.4</span>
                <span className="text-xs text-workshop-500">Mazda Standard</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-workshop-400">Custom</span>
                <span className="text-xs text-workshop-500">ECU Specific</span>
              </div>
            </div>
          </div>
        </div>

        {/* Sessions History */}
        <div className="lg:col-span-2">
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-workshop-100">Security Sessions</h2>
              <button onClick={loadSessions} className="btn-ghost text-sm">
                <RefreshCw className="w-4 h-4 mr-1" />
                Refresh
              </button>
            </div>

            {loading ? (
              <div className="flex items-center justify-center h-32">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-mazda-500"></div>
              </div>
            ) : sessions.length === 0 ? (
              <div className="text-center py-8">
                <Shield className="w-8 h-8 text-workshop-600 mx-auto mb-2" />
                <p className="text-workshop-500">No security sessions yet</p>
              </div>
            ) : (
              <div className="space-y-2">
                {sessions.map((session) => (
                  <div
                    key={session.id}
                    className="p-4 border border-workshop-800 rounded-lg hover:border-workshop-700 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {session.success ? (
                          <Unlock className="w-5 h-5 text-status-ok" />
                        ) : (
                          <Lock className="w-5 h-5 text-workshop-500" />
                        )}
                        <div>
                          <div className="font-medium text-workshop-100">
                            {session.level}
                          </div>
                          <div className="text-sm text-workshop-500">
                            {session.ECU.ecuType} • {session.algorithm || 'Unknown'}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className={`status-indicator ${
                          session.success ? 'status-online' : 'status-offline'
                        }`}>
                          {session.success ? 'Granted' : 'Pending'}
                        </div>
                        <div className="text-xs text-workshop-500 mt-1">
                          {new Date(session.createdAt).toLocaleString()}
                        </div>
                      </div>
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