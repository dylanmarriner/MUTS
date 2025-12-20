import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Activity, AlertTriangle, Settings, Download, Play, Pause } from 'lucide-react';

interface DynoMeasurement {
  rpm: number;
  torque: number;
  power: number;
  wheel_power: number;
  wheel_torque: number;
  gear?: number;
}

interface DynoRun {
  run_id: string;
  constants_version: number;
  telemetry_source: string;
  timestamp: string;
  simulation: boolean;
  max_power: number;
  max_torque: number;
  measurement_count: number;
  measurements: DynoMeasurement[];
  calculation_trace?: any[];
}

interface VehicleConstants {
  vehicle_mass: number;
  driver_fuel_mass: number;
  drag_coefficient: number;
  frontal_area: number;
  gear_ratios: number[];
  final_drive_ratio: number;
  drivetrain_efficiency: number;
  tire_radius: number;
  version: number;
  source: string;
}

/**
 * Virtual Dyno Display
 * Shows REAL physics-driven power and torque curves
 * 
 * THIS IS NOT PLACEHOLDER DATA - Curves are calculated from
 * vehicle acceleration using actual physics formulas
 */
export const VirtualDynoDisplay: React.FC = () => {
  const [currentRun, setCurrentRun] = useState<DynoRun | null>(null);
  const [constants, setConstants] = useState<VehicleConstants | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showTrace, setShowTrace] = useState(false);

  // Load vehicle constants
  useEffect(() => {
    const loadConstants = async () => {
      try {
        const result = await window.electronAPI?.invoke('dyno:getConstants');
        if (result.success) {
          setConstants(result.constants);
        } else {
          setError(result.error || 'Failed to load vehicle constants');
        }
      } catch (err) {
        setError('Cannot run dyno without vehicle constants');
      }
    };
    
    loadConstants();
  }, []);

  // Start dyno run
  const startDynoRun = async () => {
    if (!constants) {
      setError('Vehicle constants required before running dyno');
      return;
    }

    try {
      setIsRunning(true);
      setError(null);
      
      const result = await window.electronAPI?.invoke('dyno:startRun', {
        useSimulation: true,
        constantsVersion: constants.version
      });
      
      if (result.success) {
        setCurrentRun(result.run);
      } else {
        setError(result.error || 'Dyno run failed');
      }
    } catch (err) {
      setError('Failed to start dyno run');
    } finally {
      setIsRunning(false);
    }
  };

  // Prepare chart data
  const chartData = currentRun?.measurements.map(m => ({
    rpm: m.rpm,
    torque: m.torque,
    power: m.power,
    wheelPower: m.wheel_power,
    wheelTorque: m.wheel_torque,
    gear: m.gear
  })) || [];

  // Constants error display
  if (error && !constants) {
    return (
      <div className="bg-red-900 text-white p-6 rounded-lg">
        <div className="flex items-center space-x-2 mb-4">
          <AlertTriangle className="w-5 h-5" />
          <h3 className="text-lg font-semibold">DYNO UNAVAILABLE</h3>
        </div>
        <div className="space-y-2">
          <p className="text-red-200">{error}</p>
          <div className="bg-red-800 p-3 rounded text-sm">
            <p className="font-semibold mb-1">Required for dyno operation:</p>
            <ul className="list-disc list-inside space-y-1 text-red-300">
              <li>Vehicle mass (kg)</li>
              <li>Drag coefficient</li>
              <li>Gear ratios</li>
              <li>Final drive ratio</li>
              <li>Drivetrain efficiency</li>
              <li>Tire radius</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  // Loading state
  if (!constants && !error) {
    return (
      <div className="bg-gray-900 text-white p-6 rounded-lg">
        <div className="flex items-center space-x-2">
          <Activity className="w-5 h-5 animate-spin" />
          <span>Loading vehicle constants...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 text-white p-6 rounded-lg space-y-6">
      {/* Header with constants info */}
      <div className="flex items-center justify-between border-b border-gray-700 pb-4">
        <div className="flex items-center space-x-3">
          <Activity className="w-5 h-5 text-orange-400" />
          <h3 className="text-lg font-semibold">Virtual Dyno</h3>
          {constants && (
            <span className="bg-blue-900 text-blue-300 text-xs px-2 py-1 rounded">
              Constants v{constants.version}
            </span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={startDynoRun}
            disabled={isRunning || !constants}
            className="px-4 py-2 bg-orange-600 hover:bg-orange-700 disabled:bg-gray-700 disabled:cursor-not-allowed rounded-lg flex items-center space-x-2 transition-colors"
          >
            {isRunning ? <Pause size={16} /> : <Play size={16} />}
            <span>{isRunning ? 'Running...' : 'Start Dyno Run'}</span>
          </button>
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div className="bg-red-800 border border-red-700 text-red-200 p-3 rounded">
          <p className="text-sm">{error}</p>
        </div>
      )}

      {/* Current run info */}
      {currentRun && (
        <div className="bg-gray-800 p-4 rounded-lg">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3">
            <div>
              <div className="text-gray-400 text-xs">Max Power</div>
              <div className="text-xl font-bold text-orange-400">
                {currentRun.max_power.toFixed(1)} kW
              </div>
            </div>
            <div>
              <div className="text-gray-400 text-xs">Max Torque</div>
              <div className="text-xl font-bold text-purple-400">
                {currentRun.max_torque.toFixed(0)} Nm
              </div>
            </div>
            <div>
              <div className="text-gray-400 text-xs">Data Points</div>
              <div className="text-xl font-bold text-blue-400">
                {currentRun.measurement_count}
              </div>
            </div>
            <div>
              <div className="text-gray-400 text-xs">Source</div>
              <div className="text-sm">
                {currentRun.simulation ? (
                  <span className="text-yellow-400">SIMULATION</span>
                ) : (
                  <span className="text-green-400">VEHICLE</span>
                )}
              </div>
            </div>
          </div>
          
          {currentRun.simulation && (
            <div className="text-xs text-yellow-400 border-t border-gray-700 pt-2">
              ⚠️ This is a simulated dyno run using calculated acceleration data
            </div>
          )}
        </div>
      )}

      {/* Power and Torque Charts */}
      {chartData.length > 0 && (
        <div className="space-y-6">
          {/* Power Chart */}
          <div>
            <h4 className="text-sm font-semibold text-gray-400 mb-2">Power Curve</h4>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis 
                  dataKey="rpm" 
                  stroke="#9CA3AF"
                  label={{ value: 'RPM', position: 'insideBottom', offset: -5, fill: '#9CA3AF' }}
                />
                <YAxis 
                  stroke="#9CA3AF"
                  label={{ value: 'Power (kW)', angle: -90, position: 'insideLeft', fill: '#9CA3AF' }}
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }}
                  labelStyle={{ color: '#F3F4F6' }}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="power" 
                  stroke="#F97316" 
                  strokeWidth={2}
                  dot={false}
                  name="Engine Power"
                />
                <Line 
                  type="monotone" 
                  dataKey="wheelPower" 
                  stroke="#60A5FA" 
                  strokeWidth={1}
                  strokeDasharray="5 5"
                  dot={false}
                  name="Wheel Power"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Torque Chart */}
          <div>
            <h4 className="text-sm font-semibold text-gray-400 mb-2">Torque Curve</h4>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis 
                  dataKey="rpm" 
                  stroke="#9CA3AF"
                  label={{ value: 'RPM', position: 'insideBottom', offset: -5, fill: '#9CA3AF' }}
                />
                <YAxis 
                  stroke="#9CA3AF"
                  label={{ value: 'Torque (Nm)', angle: -90, position: 'insideLeft', fill: '#9CA3AF' }}
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }}
                  labelStyle={{ color: '#F3F4F6' }}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="torque" 
                  stroke="#A855F7" 
                  strokeWidth={2}
                  dot={false}
                  name="Engine Torque"
                />
                <Line 
                  type="monotone" 
                  dataKey="wheelTorque" 
                  stroke="#34D399" 
                  strokeWidth={1}
                  strokeDasharray="5 5"
                  dot={false}
                  name="Wheel Torque"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Constants Display */}
      {constants && (
        <div className="bg-gray-800 p-4 rounded-lg">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-semibold text-gray-400">Vehicle Constants Used</h4>
            <span className="text-xs text-gray-500">v{constants.version}</span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
            <div>
              <span className="text-gray-500">Mass:</span>
              <span className="ml-2">{constants.vehicle_mass} kg</span>
            </div>
            <div>
              <span className="text-gray-500">Drag Cd:</span>
              <span className="ml-2">{constants.drag_coefficient}</span>
            </div>
            <div>
              <span className="text-gray-500">Frontal Area:</span>
              <span className="ml-2">{constants.frontal_area} m²</span>
            </div>
            <div>
              <span className="text-gray-500">Gear Ratios:</span>
              <span className="ml-2">{constants.gear_ratios.length} gears</span>
            </div>
            <div>
              <span className="text-gray-500">Final Drive:</span>
              <span className="ml-2">{constants.final_drive_ratio}</span>
            </div>
            <div>
              <span className="text-gray-500">Drivetrain η:</span>
              <span className="ml-2">{(constants.drivetrain_efficiency * 100).toFixed(0)}%</span>
            </div>
          </div>
          <div className="text-xs text-gray-500 mt-2">
            Source: {constants.source}
          </div>
        </div>
      )}

      {/* Calculation Trace */}
      {currentRun?.calculation_trace && currentRun.calculation_trace.length > 0 && (
        <div>
          <button
            onClick={() => setShowTrace(!showTrace)}
            className="text-sm text-gray-400 hover:text-white transition-colors"
          >
            {showTrace ? 'Hide' : 'Show'} Calculation Trace
          </button>
          {showTrace && (
            <div className="bg-gray-800 p-4 rounded-lg mt-2 max-h-60 overflow-y-auto">
              <pre className="text-xs text-gray-300">
                {JSON.stringify(currentRun.calculation_trace, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* No data state */}
      {!currentRun && !isRunning && (
        <div className="text-center py-12 text-gray-500">
          <Activity className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>Run the dyno to see power and torque curves</p>
          <p className="text-sm mt-2">Calculations use real physics formulas with vehicle constants</p>
        </div>
      )}
    </div>
  );
};
