'use client';

import React, { useState, useEffect } from 'react';
import { ecuAPI } from '@/lib/api';
import { useHardware } from '@/contexts/HardwareContext';
import { 
  Plus, 
  Edit, 
  Trash2, 
  Search, 
  Filter,
  Cpu,
  Activity,
  CheckCircle,
  AlertCircle
} from 'lucide-react';

interface ECU {
  id: string;
  vin?: string;
  ecuType: string;
  protocol: string;
  firmwareVersion?: string;
  hardwareVersion?: string;
  serialNumber?: string;
  securityAlgorithm?: string;
  createdAt: string;
  updatedAt: string;
  diagnosticSessions: any[];
  tuningProfiles: any[];
  _count: {
    flashSessions: number;
    logs: number;
  };
}

export default function ECUManagement() {
  const [ecus, setECUs] = useState<ECU[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState('all');
  const { refreshECU } = useHardware();

  useEffect(() => {
    loadECUs();
  }, []);

  const loadECUs = async () => {
    try {
      setLoading(true);
      const response = await ecuAPI.getAll();
      setECUs(response.data);
    } catch (error) {
      console.error('Failed to load ECUs:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredECUs = ecus.filter(ecu => {
    const matchesSearch = searchTerm === '' || 
      ecu.vin?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ecu.ecuType.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ecu.serialNumber?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesFilter = filter === 'all' || ecu.protocol === filter;
    
    return matchesSearch && matchesFilter;
  });

  const protocolOptions = ['all', 'J2534', 'ISO-TP', 'UDS', 'KWP2000', 'CAN'];

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-workshop-100">ECU Management</h1>
          <p className="text-workshop-500 mt-1">
            Manage connected ECUs and their configurations
          </p>
        </div>
        <button className="btn-primary">
          <Plus className="w-4 h-4 mr-2" />
          Add ECU
        </button>
      </div>

      {/* Filters */}
      <div className="card mb-6">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-workshop-500" />
              <input
                type="text"
                placeholder="Search by VIN, ECU type, or serial..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="input pl-10 w-full"
              />
            </div>
          </div>

          {/* Protocol Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-workshop-500" />
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="input"
            >
              {protocolOptions.map(option => (
                <option key={option} value={option}>
                  {option === 'all' ? 'All Protocols' : option}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* ECU Grid */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-mazda-500"></div>
        </div>
      ) : filteredECUs.length === 0 ? (
        <div className="card text-center py-12">
          <Cpu className="w-12 h-12 text-workshop-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-workshop-100 mb-2">
            {searchTerm || filter !== 'all' ? 'No ECUs Found' : 'No ECUs Connected'}
          </h3>
          <p className="text-workshop-500">
            {searchTerm || filter !== 'all' 
              ? 'Try adjusting your search or filter criteria' 
              : 'Connect an ECU to get started'
            }
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
          {filteredECUs.map((ecu) => (
            <ECUCard key={ecu.id} ecu={ecu} onUpdate={loadECUs} />
          ))}
        </div>
      )}
    </div>
  );
}

function ECUCard({ ecu, onUpdate }: { ecu: ECU; onUpdate: () => void }) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="card hover:border-workshop-700 transition-colors">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-workshop-800 rounded-lg flex items-center justify-center">
            <Cpu className="w-5 h-5 text-mazda-400" />
          </div>
          <div>
            <h3 className="font-semibold text-workshop-100">{ecu.ecuType}</h3>
            <p className="text-sm text-workshop-500">{ecu.protocol}</p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button className="btn-ghost p-1" title="Edit">
            <Edit className="w-4 h-4" />
          </button>
          <button className="btn-ghost p-1 text-status-error hover:text-status-error" title="Delete">
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Details */}
      <div className="space-y-2 text-sm">
        {ecu.vin && (
          <div className="flex justify-between">
            <span className="text-workshop-500">VIN:</span>
            <span className="text-workshop-100 font-mono">{ecu.vin}</span>
          </div>
        )}
        
        {ecu.serialNumber && (
          <div className="flex justify-between">
            <span className="text-workshop-500">Serial:</span>
            <span className="text-workshop-100 font-mono">{ecu.serialNumber}</span>
          </div>
        )}

        {ecu.firmwareVersion && (
          <div className="flex justify-between">
            <span className="text-workshop-500">Firmware:</span>
            <span className="text-workshop-100">{ecu.firmwareVersion}</span>
          </div>
        )}

        {ecu.securityAlgorithm && (
          <div className="flex justify-between">
            <span className="text-workshop-500">Security:</span>
            <span className="text-workshop-100">{ecu.securityAlgorithm}</span>
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="mt-4 pt-4 border-t border-workshop-800">
        <div className="grid grid-cols-3 gap-2 text-center">
          <div>
            <div className="metric-value text-lg">{ecu.diagnosticSessions.length}</div>
            <div className="metric-label text-xs">Sessions</div>
          </div>
          <div>
            <div className="metric-value text-lg">{ecu.tuningProfiles.length}</div>
            <div className="metric-label text-xs">Profiles</div>
          </div>
          <div>
            <div className="metric-value text-lg">{ecu._count.flashSessions}</div>
            <div className="metric-label text-xs">Flashes</div>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="mt-4 flex gap-2">
        <button className="btn-ghost flex-1 text-sm">
          <Activity className="w-4 h-4 mr-1" />
          Diagnose
        </button>
        <button className="btn-primary flex-1 text-sm">
          <CheckCircle className="w-4 h-4 mr-1" />
          Tune
        </button>
      </div>
    </div>
  );
}