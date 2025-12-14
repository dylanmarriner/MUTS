'use client';

import React, { useState, useEffect } from 'react';
import { swasAPI, ecuAPI } from '@/lib/api';
import { useHardware } from '@/contexts/HardwareContext';
import { 
  Circle, 
  Settings, 
  Play, 
  Pause, 
  CheckCircle, 
  AlertTriangle, 
  Activity,
  TrendingDown,
  Plus,
  Edit,
  Trash2,
  Copy,
  Gauge
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface SWASConfiguration {
  id: string;
  ecuId: string;
  name: string;
  enabled: boolean;
  reductionCurve: number[][];
  maxReduction: number;
  activationAngle: number;
  deactivationAngle: number;
  responseTime: number;
  createdAt: string;
  updatedAt: string;
  ECU: {
    id: string;
    vin?: string;
    ecuType: string;
  };
}

export default function SWASInterface() {
  const [configs, setConfigs] = useState<SWASConfiguration[]>([]);
  const [selectedConfig, setSelectedConfig] = useState<SWASConfiguration | null>(null);
  const [loading, setLoading] = useState(true);
  const [testResults, setTestResults] = useState<any>(null);
  const [isTesting, setIsTesting] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    maxReduction: 50,
    activationAngle: 45,
    deactivationAngle: 30,
    responseTime: 100
  });
  const { ecu } = useHardware();

  useEffect(() => {
    loadConfigs();
  }, []);

  const loadConfigs = async () => {
    try {
      setLoading(true);
      const response = await swasAPI.getConfigurations();
      setConfigs(response.data);
      if (response.data.length > 0 && !selectedConfig) {
        setSelectedConfig(response.data[0]);
      }
    } catch (error) {
      console.error('Failed to load SWAS configs:', error);
    } finally {
      setLoading(false);
    }
  };

  const createConfig = async () => {
    if (!ecu.connected) {
      alert('No ECU connected');
      return;
    }

    try {
      const response = await swasAPI.createConfiguration({
        ecuId: ecu.activeECU!,
        ...formData,
        reductionCurve: generateDefaultCurve()
      });
      
      await loadConfigs();
      setSelectedConfig(response.data);
      resetForm();
    } catch (error) {
      console.error('Failed to create config:', error);
    }
  };

  const generateDefaultCurve = () => {
    // Generate a default reduction curve (angle vs reduction %)
    const curve = [];
    for (let angle = 0; angle <= 90; angle += 5) {
      if (angle < formData.activationAngle) {
        curve.push([angle, 0]);
      } else {
        const reduction = Math.min(
          formData.maxReduction,
          ((angle - formData.activationAngle) / (90 - formData.activationAngle)) * formData.maxReduction
        );
        curve.push([angle, reduction]);
      }
    }
    return curve;
  };

  const toggleConfig = async (configId: string, enabled: boolean) => {
    try {
      await swasAPI.toggle(configId, { enabled });
      await loadConfigs();
    } catch (error) {
      console.error('Failed to toggle config:', error);
    }
  };

  const testResponse = async (configId: string) => {
    try {
      setIsTesting(true);
      const response = await swasAPI.testResponse(configId);
      setTestResults(response.data);
    } catch (error) {
      console.error('Failed to test response:', error);
    } finally {
      setIsTesting(false);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      maxReduction: 50,
      activationAngle: 45,
      deactivationAngle: 30,
      responseTime: 100
    });
  };

  const getChartData = (curve: number[][]) => {
    return curve.map(([angle, reduction]) => ({
      angle,
      reduction,
      activation: angle >= formData.activationAngle ? 'Active' : 'Inactive'
    }));
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-violet-400 font-mono glitch">SWAS Configuration</h1>
          <p className="text-cyan-400 mt-1 font-mono text-sm">
            Steering Angle-based Torque Reduction System
          </p>
        </div>
        <button 
          onClick={() => setEditMode(!editMode)}
          className="btn-primary"
        >
          <Plus className="w-4 h-4 mr-2" />
          New Configuration
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Configuration Panel */}
        <div className="lg:col-span-1">
          <div className="card-violet">
            <h2 className="text-lg font-semibold text-violet-400 font-mono mb-4">
              {editMode ? 'Create Configuration' : 'Configurations'}
            </h2>
            
            {editMode ? (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-violet-400 mb-2 font-mono">
                    Configuration Name
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    className="input w-full"
                    placeholder="e.g., Track Mode SWAS"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-violet-400 mb-2 font-mono">
                    Max Reduction: {formData.maxReduction}%
                  </label>
                  <input
                    type="range"
                    min="10"
                    max="90"
                    value={formData.maxReduction}
                    onChange={(e) => setFormData({...formData, maxReduction: Number(e.target.value)})}
                    className="w-full"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-workshop-300 mb-2">
                    Activation Angle: {formData.activationAngle}°
                  </label>
                  <input
                    type="range"
                    min="15"
                    max="90"
                    value={formData.activationAngle}
                    onChange={(e) => setFormData({...formData, activationAngle: Number(e.target.value)})}
                    className="w-full"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-workshop-300 mb-2">
                    Deactivation Angle: {formData.deactivationAngle}°
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="60"
                    value={formData.deactivationAngle}
                    onChange={(e) => setFormData({...formData, deactivationAngle: Number(e.target.value)})}
                    className="w-full"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-workshop-300 mb-2">
                    Response Time: {formData.responseTime}ms
                  </label>
                  <input
                    type="range"
                    min="50"
                    max="500"
                    step="50"
                    value={formData.responseTime}
                    onChange={(e) => setFormData({...formData, responseTime: Number(e.target.value)})}
                    className="w-full"
                  />
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={createConfig}
                    disabled={!formData.name || !ecu.connected}
                    className="btn-primary flex-1 disabled:opacity-50"
                  >
                    <CheckCircle className="w-4 h-4 mr-1" />
                    Create
                  </button>
                  <button
                    onClick={() => {
                      setEditMode(false);
                      resetForm();
                    }}
                    className="btn-secondary flex-1"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                {loading ? (
                  <div className="flex items-center justify-center h-32">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-mazda-500"></div>
                  </div>
                ) : configs.length === 0 ? (
                  <div className="text-center py-8">
                    <Circle className="w-8 h-8 text-workshop-600 mx-auto mb-2" />
                    <p className="text-workshop-500">No SWAS configs</p>
                  </div>
                ) : (
                  configs.map((config) => (
                    <div
                      key={config.id}
                      onClick={() => setSelectedConfig(config)}
                      className={`p-3 rounded-lg border cursor-pointer transition-all ${
                        selectedConfig?.id === config.id
                          ? 'border-mazda-500 bg-workshop-800'
                          : 'border-workshop-700 hover:border-workshop-600'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          {config.enabled ? (
                            <Circle className="w-4 h-4 text-mazda-500" />
                          ) : (
                            <Circle className="w-4 h-4 text-workshop-500" />
                          )}
                          <span className="font-medium text-workshop-100">
                            {config.name}
                          </span>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleConfig(config.id, !config.enabled);
                          }}
                          className={`btn-ghost text-xs px-2 py-1 ${
                            config.enabled ? 'text-mazda-400' : 'text-workshop-400'
                          }`}
                        >
                          {config.enabled ? 'Enabled' : 'Disabled'}
                        </button>
                      </div>
                      <div className="text-xs text-workshop-400">
                        Max: {config.maxReduction}% • Act: {config.activationAngle}°
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>

          {/* SWAS Info */}
          <div className="card mt-4">
            <h3 className="text-sm font-semibold text-workshop-100 mb-3">About SWAS</h3>
            <div className="space-y-2 text-xs text-workshop-400">
              <p>
                SWAS reduces engine torque based on steering angle to prevent loss of traction during aggressive cornering.
              </p>
              <div className="pt-2 space-y-1">
                <div>• Faster response = more intervention</div>
                <div>• Higher angles = more reduction</div>
                <div>• Can be disabled for racing</div>
              </div>
            </div>
          </div>
        </div>

        {/* Configuration Details */}
        <div className="lg:col-span-2">
          {selectedConfig ? (
            <div className="space-y-6">
              {/* Config Info */}
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-workshop-100">
                    {selectedConfig.name}
                  </h2>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => testResponse(selectedConfig.id)}
                      disabled={isTesting || !selectedConfig.enabled}
                      className="btn-secondary text-sm disabled:opacity-50"
                    >
                      <Play className="w-4 h-4 mr-1" />
                      Test Response
                    </button>
                    <button className="btn-ghost text-sm">
                      <Copy className="w-4 h-4 mr-1" />
                      Duplicate
                    </button>
                    <button className="btn-ghost text-sm text-status-error">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-workshop-500">Status:</span>
                    <div className="flex items-center gap-2 mt-1">
                      {selectedConfig.enabled ? (
                        <>
                          <Circle className="w-4 h-4 text-mazda-500" />
                          <span className="text-mazda-400">Active</span>
                        </>
                      ) : (
                        <>
                          <Pause className="w-4 h-4 text-workshop-500" />
                          <span className="text-workshop-500">Disabled</span>
                        </>
                      )}
                    </div>
                  </div>
                  <div>
                    <span className="text-workshop-500">Max Reduction:</span>
                    <p className="text-workshop-100 font-bold">{selectedConfig.maxReduction}%</p>
                  </div>
                  <div>
                    <span className="text-workshop-500">Activation:</span>
                    <p className="text-workshop-100">{selectedConfig.activationAngle}°</p>
                  </div>
                  <div>
                    <span className="text-workshop-500">Response:</span>
                    <p className="text-workshop-100">{selectedConfig.responseTime}ms</p>
                  </div>
                </div>
              </div>

              {/* Reduction Curve */}
              <div className="card">
                <h3 className="text-lg font-semibold text-workshop-100 mb-4">
                  Torque Reduction Curve
                </h3>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={getChartData(selectedConfig.reductionCurve)}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis 
                      dataKey="angle" 
                      stroke="#9ca3af"
                      tick={{ fill: '#9ca3af' }}
                      label={{ value: 'Steering Angle (°)', position: 'insideBottom', offset: -5, fill: '#9ca3af' }}
                    />
                    <YAxis 
                      stroke="#9ca3af"
                      tick={{ fill: '#9ca3af' }}
                      label={{ value: 'Torque Reduction (%)', angle: -90, position: 'insideLeft', fill: '#9ca3af' }}
                    />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#1f2937', 
                        border: '1px solid #374151',
                        borderRadius: '0.5rem'
                      }}
                      labelStyle={{ color: '#f3f4f6' }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="reduction" 
                      stroke="#dc2626" 
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>

                <div className="mt-4 flex items-center justify-between text-sm">
                  <div className="flex gap-4">
                    <span className="text-workshop-500">
                      Activation: <span className="text-mazda-400">{selectedConfig.activationAngle}°</span>
                    </span>
                    <span className="text-workshop-500">
                      Deactivation: <span className="text-workshop-400">{selectedConfig.deactivationAngle}°</span>
                    </span>
                  </div>
                  <button className="btn-ghost text-sm">
                    <Edit className="w-4 h-4 mr-1" />
                    Edit Curve
                  </button>
                </div>
              </div>

              {/* Test Results */}
              {testResults && (
                <div className="card">
                  <h3 className="text-lg font-semibold text-workshop-100 mb-4">
                    Test Results
                  </h3>
                  <div className="diagnostic-grid">
                    <div className="metric-card">
                      <div className="metric-value">{testResults.avgResponse}ms</div>
                      <div className="metric-label">Avg Response</div>
                    </div>
                    <div className="metric-card">
                      <div className="metric-value">{testResults.maxReduction}%</div>
                      <div className="metric-label">Peak Reduction</div>
                    </div>
                    <div className="metric-card">
                      <div className="metric-value">{testResults.testPoints}</div>
                      <div className="metric-label">Test Points</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="card text-center py-12">
              <Circle className="w-12 h-12 text-workshop-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-workshop-100 mb-2">
                No Configuration Selected
              </h3>
              <p className="text-workshop-500">
                Select or create a SWAS configuration to view details
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}