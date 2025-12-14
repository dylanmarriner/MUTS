'use client';

import React, { useState, useEffect } from 'react';
import { torqueAPI, logAPI, ecuAPI } from '@/lib/api';
import { useHardware } from '@/contexts/HardwareContext';
import { 
  TrendingUp, 
  Play, 
  Download, 
  BarChart3, 
  Settings, 
  CheckCircle, 
  AlertTriangle,
  Plus,
  Eye,
  Copy,
  Activity
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface TorqueAdvisory {
  id: string;
  ecuId: string;
  gear: number;
  maxTorque: number;
  recommendedMax: number;
  reason?: string;
  basedOnLogId?: string;
  createdAt: string;
  ECU: {
    id: string;
    vin?: string;
    ecuType: string;
  };
  basedOnLog?: {
    id: string;
    fileName: string;
    startTime: string;
  };
}

interface Log {
  id: string;
  fileName: string;
  startTime: string;
}

export default function TorqueInterface() {
  const [advisories, setAdvisories] = useState<TorqueAdvisory[]>([]);
  const [selectedECU, setSelectedECU] = useState<string>('');
  const [logs, setLogs] = useState<Log[]>([]);
  const [selectedLog, setSelectedLog] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [safetyMargin, setSafetyMargin] = useState(10);
  const [torqueCurves, setTorqueCurves] = useState<any[]>([]);
  const [activeGear, setActiveGear] = useState(1);
  const { ecu } = useHardware();

  useEffect(() => {
    loadAdvisories();
    loadLogs();
  }, []);

  useEffect(() => {
    if (selectedECU) {
      loadAdvisoriesByECU(selectedECU);
    }
  }, [selectedECU]);

  const loadAdvisories = async () => {
    try {
      setLoading(true);
      const response = await torqueAPI.getAdvisories();
      setAdvisories(response.data);
    } catch (error) {
      console.error('Failed to load advisories:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAdvisoriesByECU = async (ecuId: string) => {
    try {
      const response = await torqueAPI.getByECU(ecuId);
      setAdvisories(response.data.advisories || []);
    } catch (error) {
      console.error('Failed to load advisories for ECU:', error);
    }
  };

  const loadLogs = async () => {
    try {
      const response = await logAPI.getLogs({ processed: true });
      setLogs(response.data);
    } catch (error) {
      console.error('Failed to load logs:', error);
    }
  };

  const generateAdvisories = async () => {
    if (!selectedLog || !ecu.connected) {
      alert('Please select a log and ensure ECU is connected');
      return;
    }

    try {
      setIsGenerating(true);
      const response = await torqueAPI.generateFromLog({
        logId: selectedLog,
        ecuId: ecu.activeECU!,
        safetyMargin: safetyMargin / 100
      });
      
      setAdvisories(response.data.advisories);
      await loadAdvisories();
    } catch (error) {
      console.error('Failed to generate advisories:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const loadTorqueCurve = async (gear: number) => {
    if (!ecu.connected) return;

    try {
      const response = await torqueAPI.getTorqueCurve(ecu.activeECU!, gear);
      setTorqueCurves(response.data.curve);
      setActiveGear(gear);
    } catch (error) {
      console.error('Failed to load torque curve:', error);
    }
  };

  const getChartData = (advisories: TorqueAdvisory[]) => {
    return advisories.map(adv => ({
      gear: adv.gear,
      maxTorque: adv.maxTorque,
      recommended: adv.recommendedMax,
      safetyMargin: adv.maxTorque - adv.recommendedMax
    })).sort((a, b) => a.gear - b.gear);
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-rose-400 font-mono glitch">Torque Advisory</h1>
          <p className="text-violet-400 mt-1 font-mono text-sm">
            Per-gear torque limits based on log analysis
          </p>
        </div>
        <button className="btn-primary">
          <Download className="w-4 h-4 mr-2" />
          Export All
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Generation Panel */}
        <div className="lg:col-span-1">
          <div className="card-rose">
            <h2 className="text-lg font-semibold text-rose-400 font-mono mb-4">Generate Advisory</h2>
            
            {!ecu.connected ? (
              <div className="text-center py-8">
                <AlertTriangle className="w-8 h-8 text-text-muted mx-auto mb-2" />
                <p className="text-text-tertiary font-mono">Connect an ECU first</p>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Log Selection */}
                <div>
                  <label className="block text-sm font-medium text-rose-400 mb-2 font-mono">
                    Select Log
                  </label>
                  <select
                    value={selectedLog}
                    onChange={(e) => setSelectedLog(e.target.value)}
                    className="input w-full"
                  >
                    <option value="">Choose a processed log...</option>
                    {logs.map((log) => (
                      <option key={log.id} value={log.id}>
                        {log.fileName}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Safety Margin */}
                <div>
                  <label className="block text-sm font-medium text-workshop-300 mb-2">
                    Safety Margin: {safetyMargin}%
                  </label>
                  <input
                    type="range"
                    min="5"
                    max="25"
                    value={safetyMargin}
                    onChange={(e) => setSafetyMargin(Number(e.target.value))}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-workshop-500 mt-1">
                    <span>5% (Aggressive)</span>
                    <span>25% (Conservative)</span>
                  </div>
                </div>

                {/* Generate Button */}
                <button
                  onClick={generateAdvisories}
                  disabled={!selectedLog || isGenerating}
                  className="btn-primary w-full disabled:opacity-50"
                >
                  <Play className="w-4 h-4 mr-2" />
                  {isGenerating ? 'Generating...' : 'Generate Advisory'}
                </button>
              </div>
            )}
          </div>

          {/* Quick Stats */}
          {advisories.length > 0 && (
            <div className="card mt-4">
              <h3 className="text-sm font-semibold text-workshop-100 mb-3">Summary</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-workshop-500">Gears Covered:</span>
                  <span className="text-workshop-100">
                    {[...new Set(advisories.map(a => a.gear))].length}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-workshop-500">Max Torque:</span>
                  <span className="text-workshop-100">
                    {Math.max(...advisories.map(a => a.maxTorque)).toFixed(0)} Nm
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-workshop-500">Avg Limit:</span>
                  <span className="text-workshop-100">
                    {(advisories.reduce((sum, a) => sum + a.recommendedMax, 0) / advisories.length).toFixed(0)} Nm
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Advisory Display */}
        <div className="lg:col-span-2">
          {advisories.length === 0 ? (
            <div className="card text-center py-12">
              <TrendingUp className="w-12 h-12 text-workshop-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-workshop-100 mb-2">
                No Torque Advisories
              </h3>
              <p className="text-workshop-500">
                Generate advisories from a processed log to get started
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Torque Chart */}
              <div className="card">
                <h3 className="text-lg font-semibold text-workshop-100 mb-4">
                  Torque Limits by Gear
                </h3>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={getChartData(advisories)}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis 
                      dataKey="gear" 
                      stroke="#9ca3af"
                      tick={{ fill: '#9ca3af' }}
                      label={{ value: 'Gear', position: 'insideBottom', offset: -5, fill: '#9ca3af' }}
                    />
                    <YAxis 
                      stroke="#9ca3af"
                      tick={{ fill: '#9ca3af' }}
                      label={{ value: 'Torque (Nm)', angle: -90, position: 'insideLeft', fill: '#9ca3af' }}
                    />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#1f2937', 
                        border: '1px solid #374151',
                        borderRadius: '0.5rem'
                      }}
                      labelStyle={{ color: '#f3f4f6' }}
                    />
                    <Legend />
                    <Line 
                      type="monotone" 
                      dataKey="maxTorque" 
                      stroke="#f59e0b" 
                      strokeWidth={2}
                      name="Measured Max"
                      dot={{ fill: '#f59e0b' }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="recommended" 
                      stroke="#dc2626" 
                      strokeWidth={2}
                      name="Recommended Limit"
                      dot={{ fill: '#dc2626' }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Gear Details */}
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-workshop-100">
                    Gear Details
                  </h3>
                  <div className="flex gap-2">
                    {[1, 2, 3, 4, 5, 6].map((gear) => (
                      <button
                        key={gear}
                        onClick={() => loadTorqueCurve(gear)}
                        className={`w-8 h-8 rounded text-sm font-medium transition-all ${
                          activeGear === gear
                            ? 'bg-mazda-600 text-white'
                            : 'bg-workshop-800 text-workshop-300 hover:bg-workshop-700'
                        }`}
                      >
                        {gear}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {advisories.map((advisory) => (
                    <div
                      key={advisory.id}
                      className="metric-card hover:border-workshop-600 transition-colors"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-2xl font-bold text-mazda-400">
                          {advisory.gear}
                        </span>
                        <span className="text-xs text-workshop-500">GEAR</span>
                      </div>
                      
                      <div className="space-y-1 text-sm">
                        <div className="flex justify-between">
                          <span className="text-workshop-500">Max:</span>
                          <span className="text-workshop-100 font-mono">
                            {advisory.maxTorque.toFixed(0)} Nm
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-workshop-500">Limit:</span>
                          <span className="text-mazda-400 font-mono">
                            {advisory.recommendedMax.toFixed(0)} Nm
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-workshop-500">Margin:</span>
                          <span className="text-status-warning font-mono">
                            -{((advisory.maxTorque - advisory.recommendedMax) / advisory.maxTorque * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>

                      {advisory.reason && (
                        <div className="mt-3 pt-3 border-t border-workshop-800">
                          <p className="text-xs text-workshop-500">
                            {advisory.reason}
                          </p>
                        </div>
                      )}

                      <div className="mt-3 flex gap-1">
                        <button className="btn-ghost text-xs flex-1">
                          <Eye className="w-3 h-3 mr-1" />
                          View
                        </button>
                        <button className="btn-ghost text-xs flex-1">
                          <Copy className="w-3 h-3 mr-1" />
                          Copy
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}