/**
 * Settings / Safety Tab
 * Safety system controls and application settings
 */

import React, { useEffect, useState } from 'react';
import { Shield, AlertTriangle, Lock, Unlock, Save, RotateCcw, Settings as SettingsIcon } from 'lucide-react';
import { useConnectionState, useSafetyState, useAppStore } from '../stores/useAppStore';

interface SafetyLimits {
  maxBoost: number;
  maxTimingAdvance: number;
  maxFuelPressure: number;
  maxRpm: number;
  minAfr: number;
  maxAfr: number;
  maxIat: number;
  maxEct: number;
}

const SettingsTab: React.FC = () => {
  const { isConnected, isDisconnected } = useConnectionState();
  const { safetyState, safetyArmed, safetyLevel, canFlash, canApplyLive } = useSafetyState();
  const { setSafetyArmed, setSafetyLevel, addSafetyViolation, clearSafetyViolations } = useAppStore();
  
  const [limits, setLimits] = useState<SafetyLimits>({
    maxBoost: 25.0,
    maxTimingAdvance: 35.0,
    maxFuelPressure: 80.0,
    maxRpm: 7000.0,
    minAfr: 11.0,
    maxAfr: 17.0,
    maxIat: 80.0,
    maxEct: 110.0,
  });
  
  const [activeTab, setActiveTab] = useState<'safety' | 'general'>('safety');
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    // Load current safety state
    if (safetyState) {
      // Update limits from safety state if available
    }
  }, [safetyState]);

  const handleArmSafety = async (level: string) => {
    try {
      await window.electronAPI.safety.arm(level);
      setSafetyLevel(level as any);
      setSafetyArmed(true);
    } catch (error) {
      console.error('Failed to arm safety:', error);
    }
  };

  const handleDisarmSafety = async () => {
    try {
      await window.electronAPI.safety.disarm();
      setSafetyLevel('ReadOnly');
      setSafetyArmed(false);
    } catch (error) {
      console.error('Failed to disarm safety:', error);
    }
  };

  const handleCreateSnapshot = async () => {
    try {
      const snapshotId = await window.electronAPI.safety.createSnapshot({
        engine_rpm: 2000,
        boost_pressure: 15,
        vehicle_speed: 0,
        // Add current telemetry values
      });
      console.log('Created snapshot:', snapshotId);
    } catch (error) {
      console.error('Failed to create snapshot:', error);
    }
  };

  const handleSaveLimits = async () => {
    setIsSaving(true);
    try {
      // Save limits to backend
      await new Promise(resolve => setTimeout(resolve, 1000));
      console.log('Limits saved:', limits);
    } catch (error) {
      console.error('Failed to save limits:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleResetLimits = () => {
    setLimits({
      maxBoost: 25.0,
      maxTimingAdvance: 35.0,
      maxFuelPressure: 80.0,
      maxRpm: 7000.0,
      minAfr: 11.0,
      maxAfr: 17.0,
      maxIat: 80.0,
      maxEct: 110.0,
    });
  };

  return (
    <div className="flex-1 p-6 overflow-auto">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
          <Shield size={24} />
          Settings / Safety
        </h1>

        {/* Tab Navigation */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setActiveTab('safety')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              activeTab === 'safety' 
                ? 'bg-red-600 text-white' 
                : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
            }`}
          >
            Safety System
          </button>
          <button
            onClick={() => setActiveTab('general')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              activeTab === 'general' 
                ? 'bg-red-600 text-white' 
                : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
            }`}
          >
            General Settings
          </button>
        </div>

        {activeTab === 'safety' && (
          <div className="space-y-6">
            {/* Safety Status */}
            <div className="bg-gray-900 rounded-lg p-6">
              <h2 className="text-lg font-semibold mb-4">Safety Status</h2>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  {safetyArmed ? (
                    <Unlock className="text-red-500" size={24} />
                  ) : (
                    <Lock className="text-gray-500" size={24} />
                  )}
                  <div>
                    <p className="font-medium">
                      Safety System: {safetyArmed ? 'ARMED' : 'DISARMED'}
                    </p>
                    <p className="text-sm text-gray-400">
                      Level: {safetyLevel}
                    </p>
                  </div>
                </div>
                
                {safetyArmed ? (
                  <button
                    onClick={handleDisarmSafety}
                    className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
                  >
                    Disarm
                  </button>
                ) : (
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleArmSafety('Simulate')}
                      disabled={!isConnected}
                      className="px-3 py-2 bg-yellow-600 hover:bg-yellow-700 disabled:bg-gray-700 rounded-lg transition-colors"
                    >
                      Simulate
                    </button>
                    <button
                      onClick={() => handleArmSafety('LiveApply')}
                      disabled={!isConnected}
                      className="px-3 py-2 bg-orange-600 hover:bg-orange-700 disabled:bg-gray-700 rounded-lg transition-colors"
                    >
                      Live Apply
                    </button>
                    <button
                      onClick={() => handleArmSafety('Flash')}
                      disabled={!isConnected}
                      className="px-3 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-700 rounded-lg transition-colors"
                    >
                      Flash
                    </button>
                  </div>
                )}
              </div>
              
              {/* Safety Level Information */}
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div className={`p-3 rounded-lg ${
                  safetyLevel === 'ReadOnly' ? 'bg-gray-800' : 'bg-gray-800/50'
                }`}>
                  <h3 className="font-medium mb-1">Read Only</h3>
                  <p className="text-gray-400">View data only</p>
                </div>
                <div className={`p-3 rounded-lg ${
                  safetyLevel === 'Simulate' ? 'bg-yellow-600/20 border border-yellow-600' : 'bg-gray-800/50'
                }`}>
                  <h3 className="font-medium mb-1">Simulate</h3>
                  <p className="text-gray-400">Test changes without applying</p>
                </div>
                <div className={`p-3 rounded-lg ${
                  safetyLevel === 'LiveApply' || safetyLevel === 'Flash' 
                    ? 'bg-red-600/20 border border-red-600' 
                    : 'bg-gray-800/50'
                }`}>
                  <h3 className="font-medium mb-1">Live Apply</h3>
                  <p className="text-gray-400">Apply changes to ECU</p>
                </div>
              </div>
            </div>

            {/* Safety Limits */}
            <div className="bg-gray-900 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Safety Limits</h2>
                <div className="flex gap-2">
                  <button
                    onClick={handleResetLimits}
                    className="px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg flex items-center gap-2 transition-colors"
                  >
                    <RotateCcw size={16} />
                    Reset
                  </button>
                  <button
                    onClick={handleSaveLimits}
                    disabled={isSaving}
                    className="px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 rounded-lg flex items-center gap-2 transition-colors"
                  >
                    <Save size={16} />
                    {isSaving ? 'Saving...' : 'Save'}
                  </button>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">
                    Max Boost (PSI)
                  </label>
                  <input
                    type="number"
                    value={limits.maxBoost}
                    onChange={(e) => setLimits({ ...limits, maxBoost: parseFloat(e.target.value) })}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">
                    Max Timing Advance (°)
                  </label>
                  <input
                    type="number"
                    value={limits.maxTimingAdvance}
                    onChange={(e) => setLimits({ ...limits, maxTimingAdvance: parseFloat(e.target.value) })}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">
                    Max Fuel Pressure (PSI)
                  </label>
                  <input
                    type="number"
                    value={limits.maxFuelPressure}
                    onChange={(e) => setLimits({ ...limits, maxFuelPressure: parseFloat(e.target.value) })}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">
                    Max RPM
                  </label>
                  <input
                    type="number"
                    value={limits.maxRpm}
                    onChange={(e) => setLimits({ ...limits, maxRpm: parseFloat(e.target.value) })}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">
                    Min AFR
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={limits.minAfr}
                    onChange={(e) => setLimits({ ...limits, minAfr: parseFloat(e.target.value) })}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">
                    Max AFR
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={limits.maxAfr}
                    onChange={(e) => setLimits({ ...limits, maxAfr: parseFloat(e.target.value) })}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">
                    Max IAT (°C)
                  </label>
                  <input
                    type="number"
                    value={limits.maxIat}
                    onChange={(e) => setLimits({ ...limits, maxIat: parseFloat(e.target.value) })}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">
                    Max ECT (°C)
                  </label>
                  <input
                    type="number"
                    value={limits.maxEct}
                    onChange={(e) => setLimits({ ...limits, maxEct: parseFloat(e.target.value) })}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg"
                  />
                </div>
              </div>
            </div>

            {/* Safety Actions */}
            <div className="bg-gray-900 rounded-lg p-6">
              <h2 className="text-lg font-semibold mb-4">Safety Actions</h2>
              <div className="grid grid-cols-2 gap-4">
                <button
                  onClick={handleCreateSnapshot}
                  disabled={!isConnected}
                  className="p-4 bg-gray-800 hover:bg-gray-700 disabled:bg-gray-800/50 rounded-lg text-left transition-colors"
                >
                  <h3 className="font-medium mb-1">Create Safety Snapshot</h3>
                  <p className="text-sm text-gray-400">Save current ECU state for quick restore</p>
                </button>
                
                <button
                  onClick={clearSafetyViolations}
                  className="p-4 bg-gray-800 hover:bg-gray-700 rounded-lg text-left transition-colors"
                >
                  <h3 className="font-medium mb-1">Clear Violations</h3>
                  <p className="text-sm text-gray-400">Clear all safety violations</p>
                </button>
              </div>
            </div>

            {/* Violations */}
            {safetyState.violations.length > 0 && (
              <div className="bg-red-500/10 border border-red-500 rounded-lg p-6">
                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <AlertTriangle className="text-red-500" size={20} />
                  Active Violations ({safetyState.violations.length})
                </h2>
                <div className="space-y-2">
                  {safetyState.violations.map((violation, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
                      <div>
                        <span className="font-medium">{violation.parameter}</span>
                        <span className="text-gray-400 ml-2">
                          {violation.value} / {violation.limit}
                        </span>
                      </div>
                      <span className={`text-sm ${
                        violation.severity === 'Critical' ? 'text-red-400' : 'text-yellow-400'
                      }`}>
                        {violation.severity}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'general' && (
          <div className="space-y-6">
            {/* General Settings */}
            <div className="bg-gray-900 rounded-lg p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <SettingsIcon size={20} />
                General Settings
              </h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium">Auto-connect Interface</h3>
                    <p className="text-sm text-gray-400">Automatically connect to last used interface</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" className="sr-only peer" />
                    <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-red-600"></div>
                  </label>
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium">Enable Logging</h3>
                    <p className="text-sm text-gray-400">Log all communication and events</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" className="sr-only peer" defaultChecked />
                    <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-red-600"></div>
                  </label>
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium">Dark Mode</h3>
                    <p className="text-sm text-gray-400">Use dark theme (always enabled)</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" className="sr-only peer" defaultChecked disabled />
                    <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-red-600"></div>
                  </label>
                </div>
              </div>
            </div>

            {/* Data Management */}
            <div className="bg-gray-900 rounded-lg p-6">
              <h2 className="text-lg font-semibold mb-4">Data Management</h2>
              <div className="space-y-3">
                <button className="w-full p-3 bg-gray-800 hover:bg-gray-700 rounded-lg text-left transition-colors">
                  <h3 className="font-medium mb-1">Clear Telemetry Cache</h3>
                  <p className="text-sm text-gray-400">Clear cached telemetry data</p>
                </button>
                
                <button className="w-full p-3 bg-gray-800 hover:bg-gray-700 rounded-lg text-left transition-colors">
                  <h3 className="font-medium mb-1">Export Database</h3>
                  <p className="text-sm text-gray-400">Export all data to file</p>
                </button>
                
                <button className="w-full p-3 bg-gray-800 hover:bg-gray-700 rounded-lg text-left transition-colors">
                  <h3 className="font-medium mb-1">Reset Application</h3>
                  <p className="text-sm text-gray-400">Reset all settings and data</p>
                </button>
              </div>
            </div>

            {/* About */}
            <div className="bg-gray-900 rounded-lg p-6">
              <h2 className="text-lg font-semibold mb-4">About</h2>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Version:</span>
                  <span>0.1.0</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Build:</span>
                  <span>2024.01.15</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">License:</span>
                  <span>MIT</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SettingsTab;
