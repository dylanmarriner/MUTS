/**
 * Live Data Tab
 * Real-time telemetry display with gauges and graphs
 */

import React, { useEffect, useState, useRef } from 'react';
import { Activity, AlertTriangle, Gauge, Play, Pause, Download } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useConnectionState, useTelemetryState, useAppStore } from '../stores/useAppStore';

interface GaugeProps {
  value: number;
  min: number;
  max: number;
  unit: string;
  label: string;
  color?: string;
  thresholds?: {
    warning: number;
    danger: number;
  };
  isConnected?: boolean;
  isStale?: boolean;
}

const Gauge: React.FC<GaugeProps> = ({ 
  value, 
  min, 
  max, 
  unit, 
  label, 
  color = '#ef4444',
  thresholds,
  isConnected = true,
  isStale = false
}) => {
  const percentage = ((value - min) / (max - min)) * 100;
  const rotation = (percentage * 180) / 100 - 90;
  
  const getColor = () => {
    if (!isConnected) return '#6b7280'; // Gray when disconnected
    if (isStale) return '#f59e0b'; // Yellow when stale
    if (!thresholds) return color;
    if (value >= thresholds.danger) return '#ef4444';
    if (value >= thresholds.warning) return '#f59e0b';
    return '#10b981';
  };

  const getDisplayValue = () => {
    if (!isConnected) return '--';
    if (isStale) return 'STALE';
    return value.toFixed(1);
  };

  return (
    <div className="bg-gray-900 rounded-lg p-6">
      <h3 className="text-sm font-medium text-gray-400 mb-4">{label}</h3>
      <div className="relative h-32 flex items-center justify-center">
        <svg className="w-full h-full" viewBox="0 0 200 100">
          {/* Background arc */}
          <path
            d="M 30 100 A 70 70 0 0 1 170 100"
            fill="none"
            stroke="#374151"
            strokeWidth="10"
            strokeLinecap="round"
          />
          {/* Value arc - hide when disconnected */}
          {(isConnected && !isStale) && (
            <path
              d="M 30 100 A 70 70 0 0 1 170 100"
              fill="none"
              stroke={getColor()}
              strokeWidth="10"
              strokeLinecap="round"
              strokeDasharray={`${percentage * 2.2} 220`}
              transform="rotate(-90 100 100)"
            />
          )}
          {/* Needle - hide when disconnected */}
          {(isConnected && !isStale) && (
            <line
              x1="100"
              y1="100"
              x2="100"
              y2="40"
              stroke={getColor()}
              strokeWidth="3"
              transform={`rotate(${rotation} 100 100)`}
            />
          )}
          <circle cx="100" cy="100" r="5" fill={getColor()} />
        </svg>
        <div className="absolute bottom-0 text-center">
          <div className="text-2xl font-bold">{getDisplayValue()}</div>
          <div className="text-xs text-gray-400">{unit}</div>
        </div>
      </div>
      {!isConnected && (
        <div className="text-center mt-2">
          <div className="text-xs text-red-500">NOT_CONNECTED</div>
        </div>
      )}
      {isStale && isConnected && (
        <div className="text-center mt-2">
          <div className="text-xs text-yellow-500">STALE DATA</div>
        </div>
      )}
    </div>
  );
};

const LiveDataTab: React.FC = () => {
  const { isConnected, isDisconnected } = useConnectionState();
  const { isStreaming, currentTelemetry, telemetryHistory } = useTelemetryState();
  const { setStreaming, addTelemetryData, clearTelemetryHistory } = useAppStore();
  
  const [isPaused, setIsPaused] = useState(false);
  const [selectedSignals, setSelectedSignals] = useState([
    'engine_rpm',
    'boost_pressure',
    'vehicle_speed',
    'lambda',
  ]);
  const subscriptionRef = useRef<boolean>(false);

  // Check if data is stale (older than 2 seconds)
  const isDataStale = currentTelemetry ? 
    (Date.now() - currentTelemetry.timestamp.getTime()) > 2000 : 
    false;

  useEffect(() => {
    if (isConnected && !isPaused) {
      startStreaming();
    } else {
      stopStreaming();
    }

    return () => stopStreaming();
  }, [isConnected, isPaused]);

  const startStreaming = () => {
    if (subscriptionRef.current) return;
    
    subscriptionRef.current = true;
    setStreaming(true);
    
    // Subscribe to telemetry data
    window.electronAPI.telemetry.subscribe((data: any) => {
      if (!isPaused) {
        const telemetry = {
          ...data,
          timestamp: new Date(data.timestamp),
        };
        addTelemetryData(telemetry);
      }
    });
  };

  const stopStreaming = () => {
    if (subscriptionRef.current) {
      window.electronAPI.telemetry.unsubscribe();
      subscriptionRef.current = false;
      setStreaming(false);
    }
  };

  const handlePause = () => {
    setIsPaused(!isPaused);
  };

  const handleExport = async () => {
    if (!currentTelemetry) return;
    
    try {
      const buffer = await window.electronAPI.telemetry.export(
        'current-session',
        'csv'
      );
      
      // Create download link
      const blob = new Blob([buffer], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `telemetry-${Date.now()}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export telemetry:', error);
    }
  };

  const getChartData = (signal: string) => {
    return telemetryHistory
      .slice(0, 100) // Last 100 samples
      .reverse()
      .map((data, index) => ({
        time: index,
        value: data.signals[signal] || 0,
      }));
  };

  if (isDisconnected) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <Activity size={64} className="mx-auto text-gray-600 mb-4" />
          <h2 className="text-xl font-semibold text-gray-400 mb-2">NO_INTERFACE_CONNECTED</h2>
          <p className="text-gray-500">Connect to an interface to view live data</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 p-6 overflow-auto">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Activity size={24} />
            Live Data
          </h1>
          
          <div className="flex items-center gap-2">
            <button
              onClick={handlePause}
              className="px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg flex items-center gap-2 transition-colors"
            >
              {isPaused ? <Play size={16} /> : <Pause size={16} />}
              {isPaused ? 'Resume' : 'Pause'}
            </button>
            
            <button
              onClick={handleExport}
              disabled={!currentTelemetry}
              className="px-3 py-2 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:cursor-not-allowed rounded-lg flex items-center gap-2 transition-colors"
            >
              <Download size={16} />
              Export
            </button>
          </div>
        </div>

        {/* Status Bar */}
        <div className="bg-gray-900 rounded-lg p-4 mb-6 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${isStreaming ? 'bg-green-500' : 'bg-gray-500'}`} />
              <span className="text-sm">
                {isStreaming ? 'Streaming' : 'Not Streaming'}
              </span>
            </div>
            
            {currentTelemetry && (
              <span className="text-sm text-gray-400">
                Sample Rate: {currentTelemetry.metadata.sampleRate} Hz
              </span>
            )}
            
            {currentTelemetry && (
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${
                  currentTelemetry.metadata.quality === 'good' ? 'bg-green-500' :
                  currentTelemetry.metadata.quality === 'fair' ? 'bg-yellow-500' :
                  currentTelemetry.metadata.quality === 'poor' ? 'bg-orange-500' :
                  'bg-red-500'
                }`} />
                <span className="text-sm text-gray-400">
                  Quality: {currentTelemetry.metadata.quality}
                </span>
              </div>
            )}
          </div>
          
          <span className="text-sm text-gray-400">
            {telemetryHistory.length} samples
          </span>
        </div>

        {/* Gauges */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <Gauge
            value={currentTelemetry?.signals.engine_rpm || 0}
            min={0}
            max={7000}
            unit="RPM"
            label="Engine Speed"
            isConnected={isConnected && !isDataStale}
            isStale={isDataStale}
            thresholds={{
              warning: 6000,
              danger: 6500,
            }}
          />
          
          <Gauge
            value={currentTelemetry?.signals.boost_pressure || 0}
            min={0}
            max={30}
            unit="PSI"
            label="Boost Pressure"
            isConnected={isConnected && !isDataStale}
            isStale={isDataStale}
            thresholds={{
              warning: 20,
              danger: 25,
            }}
          />
          
          <Gauge
            value={currentTelemetry?.signals.vehicle_speed || 0}
            min={0}
            max={160}
            unit="km/h"
            label="Vehicle Speed"
            isConnected={isConnected && !isDataStale}
            isStale={isDataStale}
          />
          
          <Gauge
            value={currentTelemetry?.signals.throttle_position || 0}
            min={0}
            max={100}
            unit="%"
            label="Throttle Position"
            isConnected={isConnected && !isDataStale}
            isStale={isDataStale}
          />
        </div>

        {/* Graphs */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          {selectedSignals.map((signal) => (
            <div key={signal} className="bg-gray-900 rounded-lg p-4">
              <h3 className="text-sm font-medium text-gray-400 mb-2">
                {signal.replace(/_/g, ' ').toUpperCase()}
              </h3>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={getChartData(signal)}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="time" stroke="#9ca3af" />
                  <YAxis stroke="#9ca3af" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1f2937',
                      border: '1px solid #374151',
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke="#ef4444"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ))}
        </div>

        {/* Data Table */}
        <div className="bg-gray-900 rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-400 mb-4">Current Values</h3>
          <div className="grid grid-cols-3 gap-4">
            {currentTelemetry ? (
              Object.entries(currentTelemetry.signals).map(([key, value]) => (
                <div key={key} className="flex justify-between">
                  <span className="text-gray-400">{key.replace(/_/g, ' ')}:</span>
                  <span className="font-mono">{value.toFixed(2)}</span>
                </div>
              ))
            ) : (
              <div className="col-span-3 text-center text-gray-500 py-8">
                No data available
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveDataTab;
