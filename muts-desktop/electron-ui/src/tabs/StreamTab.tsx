/**
 * Stream Tab
 * Raw CAN frame display and monitoring
 */

import React, { useEffect, useState } from 'react';
import { Radio, Hexagon, AlertCircle } from 'lucide-react';
import { useConnectionState, useAppStore } from '../stores/useAppStore';

interface CanFrame {
  id: number;
  extended: boolean;
  data: Uint8Array;
  timestamp: Date;
}

const StreamTab: React.FC = () => {
  const { isConnected, isDisconnected } = useConnectionState();
  const [frames, setFrames] = useState<CanFrame[]>([]);
  const [isPaused, setIsPaused] = useState(false);
  const [filter, setFilter] = useState<string>('');

  useEffect(() => {
    if (isConnected && !isPaused) {
      // In a real implementation, subscribe to raw CAN frames
      const interval = setInterval(() => {
        if (!isPaused) {
          // Simulate receiving frames
          const mockFrame: CanFrame = {
            id: Math.floor(Math.random() * 0x800),
            extended: Math.random() > 0.5,
            data: new Uint8Array(Array.from({ length: 8 }, () => Math.floor(Math.random() * 256))),
            timestamp: new Date(),
          };
          
          setFrames(prev => [mockFrame, ...prev.slice(0, 999)]);
        }
      }, 100);

      return () => clearInterval(interval);
    }
  }, [isConnected, isPaused]);

  const formatHex = (buffer: Uint8Array) => {
    return Array.from(buffer)
      .map(b => b.toString(16).padStart(2, '0').toUpperCase())
      .join(' ');
  };

  const filteredFrames = frames.filter(frame => 
    !filter || frame.id.toString(16).includes(filter.toLowerCase())
  );

  if (isDisconnected) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <Radio size={64} className="mx-auto text-gray-600 mb-4" />
          <h2 className="text-xl font-semibold text-gray-400 mb-2">NO_INTERFACE_CONNECTED</h2>
          <p className="text-gray-500">Connect to an interface to view raw CAN frames</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 p-6 overflow-auto">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
          <Radio size={24} />
          Raw Stream
        </h1>

        {/* Controls */}
        <div className="bg-gray-900 rounded-lg p-4 mb-6 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setIsPaused(!isPaused)}
              className={`px-3 py-2 rounded-lg transition-colors ${
                isPaused ? 'bg-red-600 hover:bg-red-700' : 'bg-green-600 hover:bg-green-700'
              }`}
            >
              {isPaused ? 'Paused' : 'Streaming'}
            </button>
            
            <button
              onClick={() => setFrames([])}
              className="px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
            >
              Clear
            </button>
          </div>
          
          <input
            type="text"
            placeholder="Filter by CAN ID (hex)..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm"
          />
        </div>

        {/* Frame List */}
        <div className="bg-gray-900 rounded-lg overflow-hidden">
          <div className="max-h-[600px] overflow-y-auto">
            {filteredFrames.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                {isPaused ? 'Stream paused' : 'Waiting for frames...'}
              </div>
            ) : (
              <table className="w-full text-sm">
                <thead className="bg-gray-800 sticky top-0">
                  <tr>
                    <th className="px-4 py-2 text-left">Timestamp</th>
                    <th className="px-4 py-2 text-left">ID</th>
                    <th className="px-4 py-2 text-left">Type</th>
                    <th className="px-4 py-2 text-left">DLC</th>
                    <th className="px-4 py-2 text-left font-mono">Data</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredFrames.map((frame, index) => (
                    <tr key={index} className="border-t border-gray-800 hover:bg-gray-800/50">
                      <td className="px-4 py-2 text-gray-400">
                        {frame.timestamp.toLocaleTimeString()}
                      </td>
                      <td className="px-4 py-2 font-mono">
                        {frame.id.toString(16).toUpperCase().padStart(frame.extended ? 8 : 3, '0')}
                      </td>
                      <td className="px-4 py-2">
                        <span className={`px-2 py-1 rounded text-xs ${
                          frame.extended ? 'bg-blue-500/20 text-blue-400' : 'bg-gray-700 text-gray-300'
                        }`}>
                          {frame.extended ? '29-bit' : '11-bit'}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-gray-400">{frame.data.length}</td>
                      <td className="px-4 py-2 font-mono text-xs">
                        {formatHex(frame.data)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Statistics */}
        <div className="mt-6 grid grid-cols-4 gap-4">
          <div className="bg-gray-900 rounded-lg p-4">
            <div className="text-2xl font-bold text-blue-400">{filteredFrames.length}</div>
            <div className="text-sm text-gray-400">Total Frames</div>
          </div>
          <div className="bg-gray-900 rounded-lg p-4">
            <div className="text-2xl font-bold text-green-400">
              {filteredFrames.filter(f => f.extended).length}
            </div>
            <div className="text-sm text-gray-400">29-bit Frames</div>
          </div>
          <div className="bg-gray-900 rounded-lg p-4">
            <div className="text-2xl font-bold text-yellow-400">
              {filteredFrames.filter(f => !f.extended).length}
            </div>
            <div className="text-sm text-gray-400">11-bit Frames</div>
          </div>
          <div className="bg-gray-900 rounded-lg p-4">
            <div className="text-2xl font-bold text-purple-400">
              {new Set(filteredFrames.map(f => f.id)).size}
            </div>
            <div className="text-sm text-gray-400">Unique IDs</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StreamTab;
