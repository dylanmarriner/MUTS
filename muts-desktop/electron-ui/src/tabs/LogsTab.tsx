/**
 * Logs Tab
 * Session logs, timeline, and event history
 */

import React, { useEffect, useState } from 'react';
import { FileText, Download, Search, Filter, AlertCircle, CheckCircle, Info } from 'lucide-react';
import { useConnectionState, useTelemetryState, useAppStore } from '../stores/useAppStore';

interface LogEntry {
  id: string;
  timestamp: Date;
  level: 'info' | 'warning' | 'error' | 'success';
  source: string;
  message: string;
  details?: any;
}

interface TimelineEvent {
  id: string;
  timestamp: Date;
  type: 'connection' | 'disconnection' | 'flash' | 'tuning' | 'safety' | 'error';
  title: string;
  description: string;
  icon: React.ReactNode;
}

const LogsTab: React.FC = () => {
  const { isConnected, isDisconnected } = useConnectionState();
  const { telemetryHistory } = useTelemetryState();
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [activeTab, setActiveTab] = useState<'logs' | 'timeline'>('logs');
  const [filter, setFilter] = useState('');
  const [levelFilter, setLevelFilter] = useState<string>('all');

  useEffect(() => {
    loadLogs();
    loadTimeline();
  }, []);

  const loadLogs = async () => {
    // Mock log data
    const mockLogs: LogEntry[] = [
      {
        id: '1',
        timestamp: new Date(Date.now() - 60000),
        level: 'info',
        source: 'Interface',
        message: 'Connected to SocketCAN interface',
      },
      {
        id: '2',
        timestamp: new Date(Date.now() - 45000),
        level: 'success',
        source: 'Diagnostics',
        message: 'Diagnostic session started successfully',
      },
      {
        id: '3',
        timestamp: new Date(Date.now() - 30000),
        level: 'warning',
        source: 'Safety',
        message: 'Boost pressure approaching limit',
        details: { current: 22.5, limit: 25 },
      },
      {
        id: '4',
        timestamp: new Date(Date.now() - 15000),
        level: 'info',
        source: 'Telemetry',
        message: 'Started streaming telemetry data',
      },
    ];
    setLogs(mockLogs);
  };

  const loadTimeline = () => {
    // Mock timeline data
    const mockTimeline: TimelineEvent[] = [
      {
        id: '1',
        timestamp: new Date(Date.now() - 3600000),
        type: 'connection',
        title: 'Interface Connected',
        description: 'Connected to SocketCAN interface',
        icon: <CheckCircle size={16} className="text-green-500" />,
      },
      {
        id: '2',
        timestamp: new Date(Date.now() - 1800000),
        type: 'tuning',
        title: 'Tuning Session Created',
        description: 'Created new tuning session for stage 1 map',
        icon: <Info size={16} className="text-blue-500" />,
      },
      {
        id: '3',
        timestamp: new Date(Date.now() - 900000),
        type: 'flash',
        title: 'ROM Flash Completed',
        description: 'Successfully flashed stage 1 ROM',
        icon: <CheckCircle size={16} className="text-green-500" />,
      },
      {
        id: '4',
        timestamp: new Date(Date.now() - 60000),
        type: 'safety',
        title: 'Safety System Armed',
        description: 'Armed safety system at LiveApply level',
        icon: <AlertCircle size={16} className="text-yellow-500" />,
      },
    ];
    setTimeline(mockTimeline);
  };

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'error':
        return <AlertCircle size={16} className="text-red-500" />;
      case 'warning':
        return <AlertCircle size={16} className="text-yellow-500" />;
      case 'success':
        return <CheckCircle size={16} className="text-green-500" />;
      default:
        return <Info size={16} className="text-blue-500" />;
    }
  };

  const filteredLogs = logs.filter(log => {
    const matchesFilter = !filter || 
      log.message.toLowerCase().includes(filter.toLowerCase()) ||
      log.source.toLowerCase().includes(filter.toLowerCase());
    
    const matchesLevel = levelFilter === 'all' || log.level === levelFilter;
    
    return matchesFilter && matchesLevel;
  });

  const exportLogs = () => {
    const logText = logs.map(log => 
      `[${log.timestamp.toISOString()}] [${log.level.toUpperCase()}] ${log.source}: ${log.message}`
    ).join('\n');
    
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `muts-logs-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (isDisconnected) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <FileText size={64} className="mx-auto text-gray-600 mb-4" />
          <h2 className="text-xl font-semibold text-gray-400 mb-2">NO_INTERFACE_CONNECTED</h2>
          <p className="text-gray-500">Connect to an interface to view logs and timeline</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 p-6 overflow-auto">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
          <FileText size={24} />
          Logs / Timeline
        </h1>

        {/* Tab Navigation */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setActiveTab('logs')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              activeTab === 'logs' 
                ? 'bg-red-600 text-white' 
                : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
            }`}
          >
            System Logs
          </button>
          <button
            onClick={() => setActiveTab('timeline')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              activeTab === 'timeline' 
                ? 'bg-red-600 text-white' 
                : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
            }`}
          >
            Timeline
          </button>
        </div>

        {activeTab === 'logs' && (
          <div className="space-y-6">
            {/* Log Controls */}
            <div className="bg-gray-900 rounded-lg p-4 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="relative">
                  <Search size={16} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search logs..."
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                    className="pl-10 pr-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm"
                  />
                </div>
                
                <select
                  value={levelFilter}
                  onChange={(e) => setLevelFilter(e.target.value)}
                  className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm"
                >
                  <option value="all">All Levels</option>
                  <option value="info">Info</option>
                  <option value="warning">Warning</option>
                  <option value="error">Error</option>
                  <option value="success">Success</option>
                </select>
              </div>
              
              <button
                onClick={exportLogs}
                className="px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg flex items-center gap-2 transition-colors"
              >
                <Download size={16} />
                Export
              </button>
            </div>

            {/* Log Entries */}
            <div className="bg-gray-900 rounded-lg overflow-hidden">
              <div className="max-h-[600px] overflow-y-auto">
                {filteredLogs.length === 0 ? (
                  <div className="p-8 text-center text-gray-500">
                    No logs found
                  </div>
                ) : (
                  <div className="divide-y divide-gray-800">
                    {filteredLogs.map((log) => (
                      <div key={log.id} className="p-4 hover:bg-gray-800/50 transition-colors">
                        <div className="flex items-start gap-3">
                          {getLevelIcon(log.level)}
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-medium text-sm">{log.source}</span>
                              <span className="text-xs text-gray-500">
                                {log.timestamp.toLocaleTimeString()}
                              </span>
                            </div>
                            <p className="text-sm">{log.message}</p>
                            {log.details && (
                              <pre className="mt-2 text-xs text-gray-400 bg-gray-800 p-2 rounded">
                                {JSON.stringify(log.details, null, 2)}
                              </pre>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Statistics */}
            <div className="grid grid-cols-4 gap-4">
              <div className="bg-gray-900 rounded-lg p-4">
                <div className="text-2xl font-bold text-blue-400">{logs.length}</div>
                <div className="text-sm text-gray-400">Total Logs</div>
              </div>
              <div className="bg-gray-900 rounded-lg p-4">
                <div className="text-2xl font-bold text-yellow-400">
                  {logs.filter(l => l.level === 'warning').length}
                </div>
                <div className="text-sm text-gray-400">Warnings</div>
              </div>
              <div className="bg-gray-900 rounded-lg p-4">
                <div className="text-2xl font-bold text-red-400">
                  {logs.filter(l => l.level === 'error').length}
                </div>
                <div className="text-sm text-gray-400">Errors</div>
              </div>
              <div className="bg-gray-900 rounded-lg p-4">
                <div className="text-2xl font-bold text-green-400">
                  {telemetryHistory.length}
                </div>
                <div className="text-sm text-gray-400">Telemetry Samples</div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'timeline' && (
          <div className="space-y-6">
            {/* Timeline */}
            <div className="bg-gray-900 rounded-lg p-6">
              <h2 className="text-lg font-semibold mb-4">Session Timeline</h2>
              <div className="relative">
                <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-700"></div>
                <div className="space-y-6">
                  {timeline.map((event, index) => (
                    <div key={event.id} className="relative flex items-start gap-4">
                      <div className="relative z-10 w-8 h-8 bg-gray-800 rounded-full flex items-center justify-center">
                        {event.icon}
                      </div>
                      <div className="flex-1 bg-gray-800 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="font-medium">{event.title}</h3>
                          <span className="text-xs text-gray-400">
                            {event.timestamp.toLocaleString()}
                          </span>
                        </div>
                        <p className="text-sm text-gray-400">{event.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Session Summary */}
            <div className="bg-gray-900 rounded-lg p-6">
              <h2 className="text-lg font-semibold mb-4">Session Summary</h2>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-gray-400">Session Duration:</span>
                  <p className="font-medium">1h 23m</p>
                </div>
                <div>
                  <span className="text-gray-400">Total Operations:</span>
                  <p className="font-medium">47</p>
                </div>
                <div>
                  <span className="text-gray-400">Data Points:</span>
                  <p className="font-medium">{telemetryHistory.length.toLocaleString()}</p>
                </div>
                <div>
                  <span className="text-gray-400">Errors:</span>
                  <p className="font-medium text-red-400">2</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LogsTab;
