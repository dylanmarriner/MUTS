'use client';

import React, { useState, useEffect } from 'react';
import { logAPI, ecuAPI } from '@/lib/api';
import { useHardware } from '@/contexts/HardwareContext';
import { 
  FileText, 
  Upload, 
  Download, 
  Play, 
  BarChart3, 
  TrendingUp,
  Activity,
  Clock,
  CheckCircle,
  AlertCircle,
  Eye
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface Log {
  id: string;
  ecuId: string;
  fileName: string;
  format: 'csv' | 'log' | 'bin';
  startTime: string;
  endTime?: string;
  size: number;
  processed: boolean;
  ECU: {
    id: string;
    vin?: string;
    ecuType: string;
  };
  dynoResults?: any;
  _count: {
    torquePredictions: number;
  };
}

interface TorquePrediction {
  id: string;
  logId: string;
  gear: number;
  rpm: number;
  torque: number;
  confidence: number;
}

export default function LogsInterface() {
  const [logs, setLogs] = useState<Log[]>([]);
  const [selectedLog, setSelectedLog] = useState<Log | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [torqueData, setTorqueData] = useState<TorquePrediction[]>([]);
  const [stats, setStats] = useState<any>(null);
  const { ecu } = useHardware();

  useEffect(() => {
    loadLogs();
    loadStats();
  }, []);

  const loadLogs = async () => {
    try {
      setLoading(true);
      const response = await logAPI.getLogs();
      setLogs(response.data);
      if (response.data.length > 0 && !selectedLog) {
        setSelectedLog(response.data[0]);
      }
    } catch (error) {
      console.error('Failed to load logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await logAPI.getStats();
      setStats(response.data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    const validTypes = ['.csv', '.log', '.bin'];
    const fileExt = file.name.substring(file.name.lastIndexOf('.'));
    if (!validTypes.includes(fileExt)) {
      alert(`Invalid file type. Supported: ${validTypes.join(', ')}`);
      return;
    }

    try {
      const response = await logAPI.createLog({
        ecuId: ecu.activeECU!,
        fileName: file.name,
        format: fileExt.substring(1) as 'csv' | 'log' | 'bin',
        startTime: new Date().toISOString(),
        size: file.size
      });
      
      setUploadFile(file);
      await loadLogs();
      setSelectedLog(response.data);
    } catch (error) {
      console.error('Failed to create log:', error);
    }
  };

  const processLog = async (logId: string) => {
    try {
      setIsProcessing(true);
      const response = await logAPI.processLog(logId);
      
      // Update log in list
      setLogs(prev => prev.map(l => l.id === logId ? { ...l, processed: true } : l));
      
      // Load torque predictions
      const torqueResponse = await logAPI.getTorquePredictions(logId);
      setTorqueData(torqueResponse.data);
      
      await loadLogs();
      await loadStats();
    } catch (error) {
      console.error('Failed to process log:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1024 / 1024).toFixed(1) + ' MB';
  };

  const getTorqueChartData = (data: TorquePrediction[]) => {
    // Group by RPM and average torque
    const grouped = data.reduce((acc: any, curr) => {
      const rpm = curr.rpm;
      if (!acc[rpm]) {
        acc[rpm] = { rpm, totalTorque: 0, count: 0 };
      }
      acc[rpm].totalTorque += curr.torque;
      acc[rpm].count += 1;
      return acc;
    }, {});

    return Object.values(grouped).map((item: any) => ({
      rpm: item.rpm,
      torque: item.totalTorque / item.count
    })).sort((a, b) => a.rpm - b.rpm);
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-workshop-100">Log Analysis</h1>
          <p className="text-workshop-500 mt-1">
            Upload and analyze driving logs for performance insights
          </p>
        </div>
        <label className="btn-primary cursor-pointer">
          <Upload className="w-4 h-4 mr-2" />
          Upload Log
          <input
            type="file"
            onChange={handleFileUpload}
            accept=".csv,.log,.bin"
            className="hidden"
            disabled={!ecu.connected}
          />
        </label>
      </div>

      {/* Stats Overview */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="metric-card">
            <div className="metric-value">{stats.total}</div>
            <div className="metric-label">Total Logs</div>
          </div>
          <div className="metric-card">
            <div className="metric-value">{stats.processed}</div>
            <div className="metric-label">Processed</div>
          </div>
          <div className="metric-card">
            <div className="metric-value">{formatFileSize(stats.totalSize || 0)}</div>
            <div className="metric-label">Total Size</div>
          </div>
          <div className="metric-card">
            <div className="metric-value">{stats.unprocessed}</div>
            <div className="metric-label">Pending</div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Logs List */}
        <div className="lg:col-span-1">
          <div className="card">
            <h2 className="text-lg font-semibold text-workshop-100 mb-4">Log Files</h2>
            
            {loading ? (
              <div className="flex items-center justify-center h-32">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-mazda-500"></div>
              </div>
            ) : logs.length === 0 ? (
              <div className="text-center py-8">
                <FileText className="w-8 h-8 text-workshop-600 mx-auto mb-2" />
                <p className="text-workshop-500">No logs uploaded</p>
                <button className="btn-ghost mt-2 text-sm">
                  Upload first log
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                {logs.map((log) => (
                  <div
                    key={log.id}
                    onClick={() => setSelectedLog(log)}
                    className={`p-3 rounded-lg border cursor-pointer transition-all ${
                      selectedLog?.id === log.id
                        ? 'border-mazda-500 bg-workshop-800'
                        : 'border-workshop-700 hover:border-workshop-600'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {log.processed ? (
                          <CheckCircle className="w-4 h-4 text-status-ok" />
                        ) : (
                          <AlertCircle className="w-4 h-4 text-workshop-500" />
                        )}
                        <span className="text-sm font-medium text-workshop-100 truncate">
                          {log.fileName}
                        </span>
                      </div>
                    </div>
                    <div className="text-xs text-workshop-400">
                      {log.ECU.ecuType} • {formatFileSize(log.size)}
                    </div>
                    <div className="flex gap-3 mt-2 text-xs text-workshop-500">
                      <span>{log.format.toUpperCase()}</span>
                      <span>{log._count.torquePredictions} points</span>
                    </div>
                    {!log.processed && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          processLog(log.id);
                        }}
                        disabled={isProcessing}
                        className="btn-primary text-xs mt-2 w-full disabled:opacity-50"
                      >
                        <Play className="w-3 h-3 mr-1" />
                        Process
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Log Details */}
        <div className="lg:col-span-2">
          {selectedLog ? (
            <div className="space-y-6">
              {/* Log Info */}
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-workshop-100">
                    Log Details
                  </h2>
                  <div className="flex items-center gap-2">
                    {selectedLog.processed && (
                      <button className="btn-secondary text-sm">
                        <TrendingUp className="w-4 h-4 mr-1" />
                        Generate Advisory
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
                    <span className="text-workshop-500">File:</span>
                    <p className="text-workshop-100">{selectedLog.fileName}</p>
                  </div>
                  <div>
                    <span className="text-workshop-500">ECU:</span>
                    <p className="text-workshop-100">{selectedLog.ECU.ecuType}</p>
                  </div>
                  <div>
                    <span className="text-workshop-500">Format:</span>
                    <p className="text-workshop-100">{selectedLog.format.toUpperCase()}</p>
                  </div>
                  <div>
                    <span className="text-workshop-500">Size:</span>
                    <p className="text-workshop-100">{formatFileSize(selectedLog.size)}</p>
                  </div>
                  <div>
                    <span className="text-workshop-500">Status:</span>
                    <div className="flex items-center gap-2 mt-1">
                      {selectedLog.processed ? (
                        <>
                          <CheckCircle className="w-4 h-4 text-status-ok" />
                          <span className="text-status-ok">Processed</span>
                        </>
                      ) : (
                        <>
                          <Clock className="w-4 h-4 text-workshop-500" />
                          <span className="text-workshop-500">Pending</span>
                        </>
                      )}
                    </div>
                  </div>
                  <div>
                    <span className="text-workshop-500">Data Points:</span>
                    <p className="text-workshop-100">{selectedLog._count.torquePredictions}</p>
                  </div>
                </div>
              </div>

              {/* Torque Curve */}
              {selectedLog.processed && torqueData.length > 0 && (
                <div className="card">
                  <h3 className="text-lg font-semibold text-workshop-100 mb-4">
                    Torque Curve
                  </h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={getTorqueChartData(torqueData)}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis 
                        dataKey="rpm" 
                        stroke="#9ca3af"
                        tick={{ fill: '#9ca3af' }}
                      />
                      <YAxis 
                        stroke="#9ca3af"
                        tick={{ fill: '#9ca3af' }}
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
                        dataKey="torque" 
                        stroke="#dc2626" 
                        strokeWidth={2}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                  
                  <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
                    <div className="text-center">
                      <div className="text-workshop-500">Peak Torque</div>
                      <div className="text-lg font-bold text-workshop-100">
                        {Math.max(...torqueData.map(d => d.torque)).toFixed(0)} Nm
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-workshop-500">Peak RPM</div>
                      <div className="text-lg font-bold text-workshop-100">
                        {torqueData.reduce((max, curr) => curr.torque > max.torque ? curr : max).rpm}
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-workshop-500">Avg Confidence</div>
                      <div className="text-lg font-bold text-workshop-100">
                        {(torqueData.reduce((sum, curr) => sum + curr.confidence, 0) / torqueData.length * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Dyno Results */}
              {selectedLog.processed && selectedLog.dynoResults && (
                <div className="card">
                  <h3 className="text-lg font-semibold text-workshop-100 mb-4">
                    Dyno Results
                  </h3>
                  <div className="diagnostic-grid">
                    <div className="metric-card">
                      <div className="metric-value">
                        {selectedLog.dynoResults.power.peak} HP
                      </div>
                      <div className="metric-label">
                        @ {selectedLog.dynoResults.power.atRpm} RPM
                      </div>
                    </div>
                    <div className="metric-card">
                      <div className="metric-value">
                        {selectedLog.dynoResults.torque.peak} Nm
                      </div>
                      <div className="metric-label">
                        @ {selectedLog.dynoResults.torque.atRpm} RPM
                      </div>
                    </div>
                    <div className="metric-card">
                      <div className="metric-value">
                        {selectedLog.dynoResults.power.curve.length}
                      </div>
                      <div className="metric-label">Data Points</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="card text-center py-12">
              <FileText className="w-12 h-12 text-workshop-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-workshop-100 mb-2">
                No Log Selected
              </h3>
              <p className="text-workshop-500">
                Select a log from the list to view analysis results
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}