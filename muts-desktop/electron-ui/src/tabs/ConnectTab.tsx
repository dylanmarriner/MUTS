/**
 * Connect Tab
 * Interface connection management
 */

import React, { useEffect, useState } from 'react';
import { Plug, Wifi, WifiOff, AlertCircle, CheckCircle } from 'lucide-react';
import { useConnectionState, useAppStore } from '../stores/useAppStore';

const ConnectTab: React.FC = () => {
  const { 
    connectionStatus, 
    connectedInterface, 
    availableInterfaces, 
    setAvailableInterfaces,
    setConnectionStatus,
    setConnectedInterface,
    setCurrentSession 
  } = useConnectionState();
  
  const [selectedInterface, setSelectedInterface] = useState<string>('');
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadInterfaces();
  }, []);

  const loadInterfaces = async () => {
    try {
      const interfaces = await window.electronAPI.interface.list();
      setAvailableInterfaces(interfaces);
    } catch (err) {
      console.error('Failed to load interfaces:', err);
      setError('Failed to load interfaces');
    }
  };

  const handleConnect = async () => {
    if (!selectedInterface) {
      setError('Please select an interface');
      return;
    }

    setIsConnecting(true);
    setError(null);
    setConnectionStatus('CONNECTING');

    try {
      const session = await window.electronAPI.interface.connect(selectedInterface);
      setConnectedInterface(availableInterfaces.find(i => i.id === selectedInterface) || null);
      setCurrentSession(session);
      setConnectionStatus('CONNECTED');
    } catch (err: any) {
      setError(err.message || 'Failed to connect');
      setConnectionStatus('ERROR');
    } finally {
      setIsConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      await window.electronAPI.interface.disconnect();
      setConnectedInterface(null);
      setCurrentSession(null);
      setConnectionStatus('NO_INTERFACE_CONNECTED');
    } catch (err) {
      console.error('Failed to disconnect:', err);
    }
  };

  const getStatusIcon = () => {
    switch (connectionStatus) {
      case 'CONNECTED':
        return <CheckCircle className="text-green-500" size={24} />;
      case 'CONNECTING':
        return <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500" />;
      case 'ERROR':
        return <AlertCircle className="text-red-500" size={24} />;
      default:
        return <WifiOff className="text-gray-500" size={24} />;
    }
  };

  return (
    <div className="flex-1 p-6 overflow-auto">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
          <Plug size={24} />
          Interface Connection
        </h1>

        {/* Connection Status */}
        <div className="bg-gray-900 rounded-lg p-6 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {getStatusIcon()}
              <div>
                <h2 className="text-lg font-semibold">Connection Status</h2>
                <p className="text-sm text-gray-400">
                  {connectionStatus === 'NO_INTERFACE_CONNECTED' && 'No interface connected'}
                  {connectionStatus === 'CONNECTING' && 'Connecting to interface...'}
                  {connectionStatus === 'CONNECTED' && `Connected to ${connectedInterface?.name || 'interface'}`}
                  {connectionStatus === 'ERROR' && 'Connection failed'}
                </p>
              </div>
            </div>
            
            {connectionStatus === 'CONNECTED' && (
              <button
                onClick={handleDisconnect}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
              >
                Disconnect
              </button>
            )}
          </div>
        </div>

        {/* Interface Selection */}
        {connectionStatus !== 'CONNECTED' && (
          <div className="bg-gray-900 rounded-lg p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4">Available Interfaces</h2>
            
            {availableInterfaces.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <Wifi size={48} className="mx-auto mb-2 opacity-50" />
                <p>No interfaces available</p>
                <p className="text-sm mt-2">Connect a compatible interface device</p>
              </div>
            ) : (
              <div className="space-y-3">
                {availableInterfaces.map((interfaceInfo) => (
                  <label
                    key={interfaceInfo.id}
                    className={`
                      flex items-center justify-between p-4 rounded-lg border cursor-pointer transition-all
                      ${selectedInterface === interfaceInfo.id
                        ? 'border-red-500 bg-red-500/10'
                        : 'border-gray-700 hover:border-gray-600'
                      }
                      ${!interfaceInfo.isAvailable ? 'opacity-50 cursor-not-allowed' : ''}
                    `}
                  >
                    <div className="flex items-center gap-3">
                      <input
                        type="radio"
                        name="interface"
                        value={interfaceInfo.id}
                        checked={selectedInterface === interfaceInfo.id}
                        onChange={(e) => setSelectedInterface(e.target.value)}
                        disabled={!interfaceInfo.isAvailable}
                        className="w-4 h-4 text-red-600"
                      />
                      <div>
                        <div className="font-medium">{interfaceInfo.name}</div>
                        <div className="text-sm text-gray-400">
                          Type: {interfaceInfo.interfaceType} | ID: {interfaceInfo.id}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      {interfaceInfo.isAvailable ? (
                        <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      ) : (
                        <div className="w-2 h-2 bg-gray-500 rounded-full"></div>
                      )}
                      <span className="text-sm text-gray-400">
                        {interfaceInfo.isAvailable ? 'Available' : 'Unavailable'}
                      </span>
                    </div>
                  </label>
                ))}
              </div>
            )}

            {error && (
              <div className="mt-4 p-3 bg-red-500/10 border border-red-500 rounded-lg text-red-400 text-sm">
                {error}
              </div>
            )}

            <button
              onClick={handleConnect}
              disabled={!selectedInterface || isConnecting || connectionStatus === 'CONNECTING'}
              className="mt-4 w-full px-4 py-3 bg-red-600 hover:bg-red-700 disabled:bg-gray-700 disabled:cursor-not-allowed rounded-lg transition-colors font-medium"
            >
              {isConnecting ? 'Connecting...' : 'Connect'}
            </button>
          </div>
        )}

        {/* Interface Information */}
        {connectedInterface && (
          <div className="bg-gray-900 rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4">Interface Information</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-gray-400">Name:</span>
                <p className="font-medium">{connectedInterface.name}</p>
              </div>
              <div>
                <span className="text-gray-400">Type:</span>
                <p className="font-medium">{connectedInterface.interfaceType}</p>
              </div>
              <div>
                <span className="text-gray-400">ID:</span>
                <p className="font-mono text-sm">{connectedInterface.id}</p>
              </div>
              <div>
                <span className="text-gray-400">Capabilities:</span>
                <p className="font-mono text-sm">{connectedInterface.capabilities.join(', ')}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ConnectTab;
