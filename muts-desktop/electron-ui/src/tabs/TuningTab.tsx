/**
 * Tuning Tab
 * AI tuner integration and manual tuning controls
 */

import React, { useEffect, useState } from 'react';
import { Settings, Brain, Zap, Play, Pause, AlertTriangle } from 'lucide-react';
import { useConnectionState, useSafetyState, useAppStore } from '../stores/useAppStore';

interface TuningMap {
  name: string;
  address: string;
  size: number;
  currentData: number[][];
  modifiedData: number[][];
  description: string;
}

interface AIRecommendation {
  parameter: string;
  currentValue: number;
  recommendedValue: number;
  reason: string;
  confidence: number;
}

const TuningTab: React.FC = () => {
  const { isConnected, isDisconnected } = useConnectionState();
  const { canApplyLive, safetyArmed, safetyLevel } = useSafetyState();
  const { vehicleInfo } = useAppStore();
  
  const [activeTab, setActiveTab] = useState<'manual' | 'ai'>('manual');
  const [maps, setMaps] = useState<TuningMap[]>([]);
  const [selectedMap, setSelectedMap] = useState<TuningMap | null>(null);
  const [aiRecommendations, setAiRecommendations] = useState<AIRecommendation[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [tuningSession, setTuningSession] = useState<string | null>(null);

  useEffect(() => {
    if (isConnected) {
      loadMaps();
    }
  }, [isConnected]);

  const loadMaps = async () => {
    // Mock maps data
    const mockMaps: TuningMap[] = [
      {
        name: 'Ignition Timing',
        address: '0x123456',
        size: 16,
        currentData: Array(16).fill(null).map(() => Array(16).fill(0).map(() => 10 + Math.random() * 20)),
        modifiedData: [],
        description: 'Base ignition timing map',
      },
      {
        name: 'Boost Target',
        address: '0x234567',
        size: 16,
        currentData: Array(16).fill(null).map(() => Array(16).fill(0).map(() => 5 + Math.random() * 15)),
        modifiedData: [],
        description: 'Target boost pressure map',
      },
      {
        name: 'Fueling',
        address: '0x345678',
        size: 16,
        currentData: Array(16).fill(null).map(() => Array(16).fill(0).map(() => 12 + Math.random() * 4)),
        modifiedData: [],
        description: 'Fuel injection map',
      },
    ];
    setMaps(mockMaps);
  };

  const analyzeWithAI = async () => {
    setIsAnalyzing(true);
    try {
      // Simulate AI analysis
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const mockRecommendations: AIRecommendation[] = [
        {
          parameter: 'ignition_timing',
          currentValue: 15.5,
          recommendedValue: 16.2,
          reason: 'Optimal for current boost levels',
          confidence: 0.85,
        },
        {
          parameter: 'boost_target',
          currentValue: 12.0,
          recommendedValue: 14.5,
          reason: 'Safe increase for better performance',
          confidence: 0.92,
        },
        {
          parameter: 'fueling_rpm_3000',
          currentValue: 13.2,
          recommendedValue: 13.8,
          reason: 'Slightly rich for safety at high load',
          confidence: 0.78,
        },
      ];
      
      setAiRecommendations(mockRecommendations);
    } catch (error) {
      console.error('AI analysis failed:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const createTuningSession = async () => {
    try {
      const sessionId = await window.electronAPI.tuning.createSession('changeset-001');
      setTuningSession(sessionId);
    } catch (error) {
      console.error('Failed to create tuning session:', error);
    }
  };

  const applyChanges = async () => {
    if (!tuningSession || !canApplyLive) return;
    
    try {
      const changes = [
        {
          address: 0x123456,
          oldValue: new Uint8Array([0x0F, 0x00]),
          newValue: new Uint8Array([0x10, 0x00]),
          changeType: 'SingleByte' as const,
        },
      ];
      
      await window.electronAPI.tuning.apply(tuningSession, changes);
    } catch (error) {
      console.error('Failed to apply changes:', error);
    }
  };

  if (isDisconnected) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <Settings size={64} className="mx-auto text-gray-600 mb-4" />
          <h2 className="text-xl font-semibold text-gray-400 mb-2">NO_INTERFACE_CONNECTED</h2>
          <p className="text-gray-500">Connect to an interface to access tuning features</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 p-6 overflow-auto">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
          <Settings size={24} />
          Tuning
        </h1>

        {/* Safety Warning */}
        {!safetyArmed && (
          <div className="bg-yellow-500/10 border border-yellow-500 rounded-lg p-4 mb-6 flex items-center gap-3">
            <AlertTriangle className="text-yellow-500" size={20} />
            <div>
              <p className="font-medium">Safety System Not Armed</p>
              <p className="text-sm text-gray-400">Arm the safety system in Settings to enable tuning features</p>
            </div>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setActiveTab('manual')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              activeTab === 'manual' 
                ? 'bg-red-600 text-white' 
                : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
            }`}
          >
            Manual Tuning
          </button>
          <button
            onClick={() => setActiveTab('ai')}
            className={`px-4 py-2 rounded-lg transition-colors flex items-center gap-2 ${
              activeTab === 'ai' 
                ? 'bg-red-600 text-white' 
                : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
            }`}
          >
            <Brain size={16} />
            AI Tuner
          </button>
        </div>

        {activeTab === 'manual' && (
          <div className="space-y-6">
            {/* Map Selection */}
            <div className="bg-gray-900 rounded-lg p-6">
              <h2 className="text-lg font-semibold mb-4">Select Map</h2>
              <div className="grid grid-cols-3 gap-4">
                {maps.map((map) => (
                  <button
                    key={map.name}
                    onClick={() => setSelectedMap(map)}
                    className={`p-4 rounded-lg border transition-all text-left ${
                      selectedMap?.name === map.name
                        ? 'border-red-500 bg-red-500/10'
                        : 'border-gray-700 hover:border-gray-600'
                    }`}
                  >
                    <h3 className="font-medium">{map.name}</h3>
                    <p className="text-sm text-gray-400 mt-1">{map.description}</p>
                    <p className="text-xs text-gray-500 mt-2 font-mono">{map.address}</p>
                  </button>
                ))}
              </div>
            </div>

            {/* Map Editor */}
            {selectedMap && (
              <div className="bg-gray-900 rounded-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold">{selectedMap.name} Editor</h2>
                  <div className="flex items-center gap-2">
                    {!tuningSession && (
                      <button
                        onClick={createTuningSession}
                        disabled={!canApplyLive}
                        className="px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 rounded-lg text-sm transition-colors"
                      >
                        Create Session
                      </button>
                    )}
                    <button
                      onClick={applyChanges}
                      disabled={!tuningSession || !canApplyLive}
                      className="px-3 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-700 rounded-lg text-sm transition-colors flex items-center gap-2"
                    >
                      <Zap size={14} />
                      Apply Live
                    </button>
                  </div>
                </div>
                
                {/* Simplified table view */}
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-800">
                        <th className="text-left p-2">RPM</th>
                        {Array.from({ length: 8 }, (_, i) => (
                          <th key={i} className="text-center p-2 font-mono text-xs">
                            {(i * 2).toString()}k
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {selectedMap.currentData.slice(0, 8).map((row, i) => (
                        <tr key={i} className="border-b border-gray-800">
                          <td className="p-2 font-mono">{(i * 500).toString()}</td>
                          {row.slice(0, 8).map((val, j) => (
                            <td key={j} className="p-2 text-center font-mono">
                              {val.toFixed(1)}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'ai' && (
          <div className="space-y-6">
            {/* AI Analysis */}
            <div className="bg-gray-900 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold flex items-center gap-2">
                  <Brain size={20} />
                  AI Analysis
                </h2>
                <button
                  onClick={analyzeWithAI}
                  disabled={isAnalyzing}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 rounded-lg transition-colors flex items-center gap-2"
                >
                  {isAnalyzing ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                  ) : (
                    <Play size={16} />
                  )}
                  {isAnalyzing ? 'Analyzing...' : 'Analyze'}
                </button>
              </div>

              {aiRecommendations.length > 0 ? (
                <div className="space-y-3">
                  {aiRecommendations.map((rec, index) => (
                    <div key={index} className="bg-gray-800 rounded-lg p-4">
                      <div className="flex items-start justify-between">
                        <div>
                          <h3 className="font-medium">{rec.parameter.replace(/_/g, ' ').toUpperCase()}</h3>
                          <p className="text-sm text-gray-400 mt-1">{rec.reason}</p>
                          <div className="flex items-center gap-4 mt-2 text-sm">
                            <span>Current: {rec.currentValue.toFixed(2)}</span>
                            <span>→</span>
                            <span className="text-green-400">Recommended: {rec.recommendedValue.toFixed(2)}</span>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm text-gray-400">Confidence</div>
                          <div className="text-lg font-bold text-purple-400">
                            {(rec.confidence * 100).toFixed(0)}%
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <Brain size={48} className="mx-auto mb-2 opacity-50" />
                  <p>Click Analyze to get AI recommendations</p>
                </div>
              )}
            </div>

            {/* AI Settings */}
            <div className="bg-gray-900 rounded-lg p-6">
              <h2 className="text-lg font-semibold mb-4">AI Tuning Settings</h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium">Aggressiveness</h3>
                    <p className="text-sm text-gray-400">How aggressive the AI recommendations should be</p>
                  </div>
                  <select className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg">
                    <option>Conservative</option>
                    <option>Moderate</option>
                    <option>Aggressive</option>
                  </select>
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium">Target Power</h3>
                    <p className="text-sm text-gray-400">Target horsepower increase</p>
                  </div>
                  <select className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg">
                    <option>+10 hp</option>
                    <option>+25 hp</option>
                    <option>+50 hp</option>
                    <option>+75 hp</option>
                    <option>+100 hp</option>
                  </select>
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium">Fuel Type</h3>
                    <p className="text-sm text-gray-400">Primary fuel type for tuning</p>
                  </div>
                  <select className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg">
                    <option>91-93 Octane</option>
                    <option>E85</option>
                    <option>Race Fuel</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TuningTab;
