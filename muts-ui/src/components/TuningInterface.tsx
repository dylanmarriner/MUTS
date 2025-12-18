'use client';

import React, { useState, useEffect } from 'react';
import { tuningAPI, ecuAPI } from '@/lib/api';
import { useHardware } from '@/contexts/HardwareContext';
import { 
  Plus, 
  Save, 
  Download, 
  Upload, 
  CheckCircle, 
  AlertTriangle, 
  Grid3x3,
  Edit,
  Eye,
  Copy,
  Trash2
} from 'lucide-react';

interface TuningMap {
  id: string;
  tableName: string;
  axisX: number[];
  axisY: number[];
  values: number[][];
  description?: string;
}

interface TuningProfile {
  id: string;
  name: string;
  description?: string;
  isActive: boolean;
  isBase: boolean;
  createdAt: string;
  updatedAt: string;
  ECU: {
    id: string;
    vin?: string;
    ecuType: string;
  };
  _count: {
    ignitionMaps: number;
    fuelMaps: number;
    boostMaps: number;
    limiterMaps: number;
    safetyChecks: number;
  };
}

export default function TuningInterface() {
  const [profiles, setProfiles] = useState<TuningProfile[]>([]);
  const [selectedProfile, setSelectedProfile] = useState<TuningProfile | null>(null);
  const [activeTab, setActiveTab] = useState<'ignition' | 'fuel' | 'boost' | 'limiters'>('ignition');
  const [maps, setMaps] = useState<TuningMap[]>([]);
  const [editingMap, setEditingMap] = useState<TuningMap | null>(null);
  const [loading, setLoading] = useState(true);
  const { ecu } = useHardware();

  useEffect(() => {
    loadProfiles();
  }, []);

  useEffect(() => {
    if (selectedProfile) {
      loadMaps(activeTab);
    }
  }, [selectedProfile, activeTab]);

  const loadProfiles = async () => {
    try {
      setLoading(true);
      const response = await tuningAPI.getProfiles();
      setProfiles(response.data);
      if (response.data.length > 0 && !selectedProfile) {
        setSelectedProfile(response.data[0]);
      }
    } catch (error) {
      console.error('Failed to load profiles:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadMaps = async (type: string) => {
    if (!selectedProfile) return;

    try {
      let response;
      switch (type) {
        case 'ignition':
          response = await tuningAPI.getProfile(selectedProfile.id);
          setMaps(response.data.ignitionMaps || []);
          break;
        case 'fuel':
          response = await tuningAPI.getProfile(selectedProfile.id);
          setMaps(response.data.fuelMaps || []);
          break;
        case 'boost':
          response = await tuningAPI.getProfile(selectedProfile.id);
          setMaps(response.data.boostMaps || []);
          break;
        case 'limiters':
          response = await tuningAPI.getProfile(selectedProfile.id);
          setMaps(response.data.limiterMaps || []);
          break;
      }
    } catch (error) {
      console.error('Failed to load maps:', error);
    }
  };

  const activateProfile = async (profileId: string) => {
    try {
      await tuningAPI.activateProfile(profileId);
      await loadProfiles();
    } catch (error) {
      console.error('Failed to activate profile:', error);
    }
  };

  const getColorForValue = (value: number, type: string) => {
    if (type === 'ignition') {
      // Timing: Blue (retarded) -> Red (advanced)
      const normalized = (value + 20) / 40; // Assuming -20 to +20 range
      const hue = (1 - normalized) * 240; // Blue to Red
      return `hsl(${hue}, 70%, 50%)`;
    } else if (type === 'fuel') {
      // AFR: Blue (lean) -> Red (rich)
      const normalized = (value - 10) / 10; // Assuming 10:1 to 20:1 range
      const hue = (1 - normalized) * 240;
      return `hsl(${hue}, 70%, 50%)`;
    } else if (type === 'boost') {
      // Boost: Green (low) -> Red (high)
      const normalized = value / 30; // Assuming 0-30 PSI range
      const hue = (1 - normalized) * 120; // Green to Red
      return `hsl(${hue}, 70%, 50%)`;
    }
    return '#374151';
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-cyan-400 font-mono glitch">Tuning</h1>
          <p className="text-violet-400 mt-1 font-mono text-sm">
            Create and manage ECU tuning profiles
          </p>
        </div>
        <button className="btn-primary">
          <Plus className="w-4 h-4 mr-2" />
          New Profile
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Profiles List */}
        <div className="lg:col-span-1">
          <div className="card">
            <h2 className="text-lg font-semibold text-workshop-100 mb-4">Profiles</h2>
            
            {loading ? (
              <div className="flex items-center justify-center h-32">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-mazda-500"></div>
              </div>
            ) : profiles.length === 0 ? (
              <div className="text-center py-8">
                <Grid3x3 className="w-8 h-8 text-workshop-600 mx-auto mb-2" />
                <p className="text-workshop-500">No profiles yet</p>
              </div>
            ) : (
              <div className="space-y-2">
                {profiles.map((profile) => (
                  <div
                    key={profile.id}
                    onClick={() => setSelectedProfile(profile)}
                    className={`p-3 rounded-lg border cursor-pointer transition-all ${
                      selectedProfile?.id === profile.id
                        ? 'border-mazda-500 bg-workshop-800'
                        : 'border-workshop-700 hover:border-workshop-600'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-workshop-100">
                        {profile.name}
                      </span>
                      {profile.isActive && (
                        <CheckCircle className="w-4 h-4 text-status-ok" />
                      )}
                    </div>
                    <div className="text-xs text-workshop-400">
                      {profile.ECU.ecuType}
                    </div>
                    <div className="flex gap-3 mt-2 text-xs text-workshop-500">
                      <span>Ign: {profile._count.ignitionMaps}</span>
                      <span>Fuel: {profile._count.fuelMaps}</span>
                      <span>Boost: {profile._count.boostMaps}</span>
                    </div>
                    {!profile.isActive && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          activateProfile(profile.id);
                        }}
                        className="btn-secondary text-xs mt-2 w-full"
                      >
                        Activate
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Maps Editor */}
        <div className="lg:col-span-3">
          {selectedProfile ? (
            <div className="space-y-6">
              {/* Profile Info */}
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h2 className="text-lg font-semibold text-workshop-100">
                      {selectedProfile.name}
                    </h2>
                    <p className="text-sm text-workshop-500">
                      {selectedProfile.description || 'No description'}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button className="btn-secondary text-sm">
                      <Copy className="w-4 h-4 mr-1" />
                      Duplicate
                    </button>
                    <button className="btn-ghost text-sm">
                      <Download className="w-4 h-4 mr-1" />
                      Export
                    </button>
                    <button className="btn-primary text-sm">
                      <Save className="w-4 h-4 mr-1" />
                      Save
                    </button>
                  </div>
                </div>
              </div>

              {/* Map Type Tabs */}
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex gap-1 bg-workshop-800 rounded-lg p-1">
                    {[
                      { id: 'ignition', label: 'Ignition' },
                      { id: 'fuel', label: 'Fuel' },
                      { id: 'boost', label: 'Boost' },
                      { id: 'limiters', label: 'Limiters' }
                    ].map((tab) => (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id as any)}
                        className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                          activeTab === tab.id
                            ? 'bg-mazda-600 text-white'
                            : 'text-workshop-400 hover:text-workshop-100'
                        }`}
                      >
                        {tab.label}
                      </button>
                    ))}
                  </div>
                  <button className="btn-ghost text-sm">
                    <Plus className="w-4 h-4 mr-1" />
                    Add Map
                  </button>
                </div>

                {/* Maps List */}
                {maps.length === 0 ? (
                  <div className="text-center py-8">
                    <Grid3x3 className="w-8 h-8 text-workshop-600 mx-auto mb-2" />
                    <p className="text-workshop-500">No {activeTab} maps found</p>
                    <button className="btn-secondary mt-2 text-sm">
                      Create First Map
                    </button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {maps.map((map) => (
                      <MapGrid
                        key={map.id}
                        map={map}
                        type={activeTab}
                        onEdit={() => setEditingMap(map)}
                      />
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="card text-center py-12">
              <Grid3x3 className="w-12 h-12 text-workshop-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-workshop-100 mb-2">
                No Profile Selected
              </h3>
              <p className="text-workshop-500">
                Select a profile to view and edit its tuning maps
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function MapGrid({ map, type, onEdit }: { 
  map: TuningMap; 
  type: string; 
  onEdit: () => void;
}) {
  const [hoveredCell, setHoveredCell] = useState<{x: number, y: number} | null>(null);
  const [editMode, setEditMode] = useState(false);

  const getValueColor = (value: number) => {
    if (type === 'ignition') {
      const normalized = (value + 20) / 40;
      const hue = (1 - normalized) * 240;
      return `hsl(${hue}, 70%, 50%)`;
    } else if (type === 'fuel') {
      const normalized = (value - 10) / 10;
      const hue = (1 - normalized) * 240;
      return `hsl(${hue}, 70%, 50%)`;
    } else if (type === 'boost') {
      const normalized = Math.min(value / 30, 1);
      const hue = (1 - normalized) * 120;
      return `hsl(${hue}, 70%, 50%)`;
    }
    return '#374151';
  };

  return (
    <div className="border border-workshop-800 rounded-lg overflow-hidden">
      <div className="bg-workshop-800 px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h4 className="font-medium text-workshop-100">{map.tableName}</h4>
          {map.description && (
            <span className="text-sm text-workshop-500">{map.description}</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setEditMode(!editMode)}
            className={`btn-ghost text-sm ${editMode ? 'text-mazda-400' : ''}`}
          >
            <Edit className="w-4 h-4" />
          </button>
          <button className="btn-ghost text-sm">
            <Eye className="w-4 h-4" />
          </button>
          <button className="btn-ghost text-sm text-status-error">
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="p-4 bg-workshop-900">
        <div className="inline-block">
          {/* Header Row */}
          <div className="flex">
            <div className="w-16 h-8"></div>
            {map.axisX.map((x, i) => (
              <div key={i} className="w-12 h-8 text-xs text-workshop-500 text-center">
                {x}
              </div>
            ))}
          </div>

          {/* Grid */}
          {map.values.map((row, y) => (
            <div key={y} className="flex">
              <div className="w-16 h-8 text-xs text-workshop-500 flex items-center pr-2 justify-end">
                {map.axisY[y]}
              </div>
              {row.map((value, x) => (
                <div
                  key={x}
                  className="w-12 h-8 text-xs text-center flex items-center justify-center border border-workshop-800 cursor-pointer relative group"
                  style={{ backgroundColor: getValueColor(value) }}
                  onMouseEnter={() => setHoveredCell({x, y})}
                  onMouseLeave={() => setHoveredCell(null)}
                  onClick={() => editMode && console.log('Edit cell', x, y, value)}
                >
                  <span className="text-white font-mono font-medium">
                    {value.toFixed(1)}
                  </span>
                  
                  {/* Tooltip */}
                  {hoveredCell?.x === x && hoveredCell?.y === y && (
                    <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-workshop-700 text-white text-xs rounded whitespace-nowrap z-10">
                      <div>RPM: {map.axisX[x]}</div>
                      <div>Load: {map.axisY[y]}</div>
                      <div>Value: {value}</div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ))}
        </div>

        {/* Legend */}
        <div className="mt-4 flex items-center justify-between text-xs">
          <div className="flex items-center gap-4">
            <span className="text-workshop-500">Legend:</span>
            {type === 'ignition' && (
              <>
                <span className="flex items-center gap-1">
                  <div className="w-4 h-4 rounded" style={{backgroundColor: 'hsl(240, 70%, 50%)'}}></div>
                  Retarded
                </span>
                <span className="flex items-center gap-1">
                  <div className="w-4 h-4 rounded" style={{backgroundColor: 'hsl(0, 70%, 50%)'}}></div>
                  Advanced
                </span>
              </>
            )}
            {type === 'fuel' && (
              <>
                <span className="flex items-center gap-1">
                  <div className="w-4 h-4 rounded" style={{backgroundColor: 'hsl(240, 70%, 50%)'}}></div>
                  Lean
                </span>
                <span className="flex items-center gap-1">
                  <div className="w-4 h-4 rounded" style={{backgroundColor: 'hsl(0, 70%, 50%)'}}></div>
                  Rich
                </span>
              </>
            )}
          </div>
          {editMode && (
            <span className="text-mazda-400">Click cells to edit</span>
          )}
        </div>
      </div>
    </div>
  );
}