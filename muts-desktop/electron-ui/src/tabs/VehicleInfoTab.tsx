/**
 * Vehicle Info Tab
 * Displays vehicle identification and ECU information
 */

import React, { useEffect, useState } from 'react';
import { Car, Info, Cpu } from 'lucide-react';
import { useConnectionState, useAppStore } from '../stores/useAppStore';

const VehicleInfoTab: React.FC = () => {
  const { vehicleInfo, setVehicleInfo } = useAppStore();
  const { isConnected, isDisconnected } = useConnectionState();
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (isConnected) {
      loadVehicleInfo();
    }
  }, [isConnected]);

  const loadVehicleInfo = async () => {
    setIsLoading(true);
    try {
      // In a real implementation, this would query the ECU for vehicle info
      // For now, use mock data
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setVehicleInfo({
        vin: 'JM1BK123456789012',
        make: 'Mazda',
        model: 'Speed3',
        year: 2010,
        ecuType: 'Mazda ECU',
        calibrationId: 'A2YC9001',
      });
    } catch (error) {
      console.error('Failed to load vehicle info:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isDisconnected) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <Car size={64} className="mx-auto text-gray-600 mb-4" />
          <h2 className="text-xl font-semibold text-gray-400 mb-2">No Interface Connected</h2>
          <p className="text-gray-500">Connect to an interface to read vehicle information</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 p-6 overflow-auto">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
          <Car size={24} />
          Vehicle Information
        </h1>

        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500"></div>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-6">
            {/* Vehicle Details */}
            <div className="bg-gray-900 rounded-lg p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Info size={20} />
                Vehicle Details
              </h2>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-400">VIN:</span>
                  <span className="font-mono">{vehicleInfo.vin || 'Unknown'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Make:</span>
                  <span>{vehicleInfo.make || 'Unknown'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Model:</span>
                  <span>{vehicleInfo.model || 'Unknown'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Year:</span>
                  <span>{vehicleInfo.year || 'Unknown'}</span>
                </div>
              </div>
            </div>

            {/* ECU Details */}
            <div className="bg-gray-900 rounded-lg p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Cpu size={20} />
                ECU Information
              </h2>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-400">ECU Type:</span>
                  <span>{vehicleInfo.ecuType || 'Unknown'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Calibration ID:</span>
                  <span className="font-mono">{vehicleInfo.calibrationId || 'Unknown'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Protocol:</span>
                  <span>ISO-TP / CAN</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">OBD Port:</span>
                  <span>16-pin</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Additional Information */}
        <div className="mt-6 bg-gray-900 rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">System Status</h2>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-500">OK</div>
              <div className="text-sm text-gray-400">Communication</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-500">OK</div>
              <div className="text-sm text-gray-400">Security Access</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-500">OK</div>
              <div className="text-sm text-gray-400">Diagnostics</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VehicleInfoTab;
