'use client';

import React, { useState, useEffect } from 'react';
import { agentAPI } from '@/lib/api';
import { useHardware } from '@/contexts/HardwareContext';
import { 
  Users, 
  Play, 
  Square, 
  CheckCircle, 
  AlertTriangle, 
  Clock,
  Activity,
  Settings,
  RefreshCw,
  Trash2,
  Eye,
  Zap
} from 'lucide-react';

interface Agent {
  name: string;
  status: 'idle' | 'running' | 'error' | 'completed';
  currentTask?: string;
  lastActivity: string;
  taskCount: number;
  errorCount: number;
  successCount: number;
  uptime: number;
  memoryUsage: number;
}

interface CoordinationStatus {
  totalAgents: number;
  running: number;
  idle: number;
  error: number;
  completed: number;
  systemLoad: number;
}

export default function AgentsInterface() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [coordination, setCoordination] = useState<CoordinationStatus | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [taskInput, setTaskInput] = useState('');
  const { isPolling } = useHardware();

  useEffect(() => {
    loadAgents();
    loadCoordination();
  }, []);

  const loadAgents = async () => {
    try {
      setLoading(true);
      const response = await agentAPI.getStatuses();
      setAgents(response.data);
    } catch (error) {
      console.error('Failed to load agents:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCoordination = async () => {
    try {
      const response = await agentAPI.getCoordinationStatus();
      setCoordination(response.data);
    } catch (error) {
      console.error('Failed to load coordination status:', error);
    }
  };

  const refreshAll = async () => {
    setIsRefreshing(true);
    await Promise.all([loadAgents(), loadCoordination()]);
    setIsRefreshing(false);
  };

  const startTask = async (agentName: string) => {
    if (!taskInput.trim()) {
      alert('Please enter a task description');
      return;
    }

    try {
      await agentAPI.startTask(agentName, {
        task: taskInput,
        priority: 'normal'
      });
      
      setTaskInput('');
      await loadAgents();
      await loadCoordination();
    } catch (error) {
      console.error('Failed to start task:', error);
    }
  };

  const completeTask = async (agentName: string) => {
    try {
      await agentAPI.completeTask(agentName, {
        result: 'Task completed successfully',
        success: true
      });
      
      await loadAgents();
      await loadCoordination();
    } catch (error) {
      console.error('Failed to complete task:', error);
    }
  };

  const resetAllAgents = async () => {
    if (!confirm('Are you sure you want to reset all agents? This will clear all active tasks.')) {
      return;
    }

    try {
      await agentAPI.resetAll();
      await loadAgents();
      await loadCoordination();
    } catch (error) {
      console.error('Failed to reset agents:', error);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Activity className="w-4 h-4 text-cyan-400 animate-pulse" />;
      case 'idle':
        return <Clock className="w-4 h-4 text-text-muted" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'error':
        return <AlertTriangle className="w-4 h-4 text-red-400" />;
      default:
        return <Clock className="w-4 h-4 text-text-muted" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'text-cyan-400';
      case 'idle':
        return 'text-text-muted';
      case 'completed':
        return 'text-green-400';
      case 'error':
        return 'text-red-400';
      default:
        return 'text-text-muted';
    }
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-cyan-400 font-mono glitch">Agent Coordination</h1>
          <p className="text-violet-400 mt-1 font-mono text-sm">
            Monitor and coordinate autonomous system agents
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={refreshAll}
            disabled={isRefreshing}
            className="btn-secondary text-sm disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 mr-1 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={resetAllAgents}
            className="btn-ghost text-sm text-status-error"
          >
            <Square className="w-4 h-4 mr-1" />
            Reset All
          </button>
        </div>
      </div>

      {/* Coordination Overview */}
      {coordination && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
          <div className="metric-card">
            <div className="metric-value">{coordination.totalAgents}</div>
            <div className="metric-label">Total Agents</div>
          </div>
          <div className="metric-card">
            <div className="metric-value text-mazda-400">{coordination.running}</div>
            <div className="metric-label">Running</div>
          </div>
          <div className="metric-card">
            <div className="metric-value text-workshop-400">{coordination.idle}</div>
            <div className="metric-label">Idle</div>
          </div>
          <div className="metric-card">
            <div className="metric-value text-status-error">{coordination.error}</div>
            <div className="metric-label">Errors</div>
          </div>
          <div className="metric-card">
            <div className="metric-value text-status-ok">{coordination.completed}</div>
            <div className="metric-label">Completed</div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Agents List */}
        <div className="lg:col-span-1">
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-workshop-100">Agents</h2>
              <div className="flex items-center gap-1">
                <div className={`w-2 h-2 rounded-full ${isPolling ? 'bg-status-ok animate-pulse' : 'bg-status-offline'}`} />
                <span className="text-xs text-workshop-500">
                  {isPolling ? 'Live' : 'Offline'}
                </span>
              </div>
            </div>
            
            {loading ? (
              <div className="flex items-center justify-center h-32">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-mazda-500"></div>
              </div>
            ) : agents.length === 0 ? (
              <div className="text-center py-8">
                <Users className="w-8 h-8 text-workshop-600 mx-auto mb-2" />
                <p className="text-workshop-500">No agents found</p>
              </div>
            ) : (
              <div className="space-y-2">
                {agents.map((agent) => (
                  <div
                    key={agent.name}
                    onClick={() => setSelectedAgent(agent)}
                    className={`p-3 rounded-lg border cursor-pointer transition-all ${
                      selectedAgent?.name === agent.name
                        ? 'border-mazda-500 bg-workshop-800'
                        : 'border-workshop-700 hover:border-workshop-600'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(agent.status)}
                        <span className="font-medium text-workshop-100">
                          {agent.name}
                        </span>
                      </div>
                      <span className={`text-sm font-medium ${getStatusColor(agent.status)}`}>
                        {agent.status}
                      </span>
                    </div>
                    <div className="text-xs text-workshop-400">
                      {agent.currentTask || 'No active task'}
                    </div>
                    <div className="flex gap-3 mt-2 text-xs text-workshop-500">
                      <span>Tasks: {agent.taskCount}</span>
                      <span>Success: {agent.successCount}</span>
                      {agent.errorCount > 0 && (
                        <span className="text-status-error">Errors: {agent.errorCount}</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Agent Details */}
        <div className="lg:col-span-2">
          {selectedAgent ? (
            <div className="space-y-6">
              {/* Agent Info */}
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-workshop-100">
                    {selectedAgent.name}
                  </h2>
                  <div className="flex items-center gap-2">
                    {selectedAgent.status === 'running' && (
                      <button
                        onClick={() => completeTask(selectedAgent.name)}
                        className="btn-secondary text-sm"
                      >
                        <CheckCircle className="w-4 h-4 mr-1" />
                        Complete Task
                      </button>
                    )}
                    <button className="btn-ghost text-sm">
                      <Eye className="w-4 h-4 mr-1" />
                      View History
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-workshop-500">Status:</span>
                    <div className="flex items-center gap-2 mt-1">
                      {getStatusIcon(selectedAgent.status)}
                      <span className={`capitalize ${getStatusColor(selectedAgent.status)}`}>
                        {selectedAgent.status}
                      </span>
                    </div>
                  </div>
                  <div>
                    <span className="text-workshop-500">Uptime:</span>
                    <p className="text-workshop-100">{selectedAgent.uptime}s</p>
                  </div>
                  <div>
                    <span className="text-workshop-500">Memory:</span>
                    <p className="text-workshop-100">{selectedAgent.memoryUsage}MB</p>
                  </div>
                  <div>
                    <span className="text-workshop-500">Last Activity:</span>
                    <p className="text-workshop-100">
                      {new Date(selectedAgent.lastActivity).toLocaleTimeString()}
                    </p>
                  </div>
                </div>

                {selectedAgent.currentTask && (
                  <div className="mt-4 p-3 bg-workshop-800 rounded-lg">
                    <div className="text-sm text-workshop-500 mb-1">Current Task:</div>
                    <div className="text-workshop-100">{selectedAgent.currentTask}</div>
                  </div>
                )}
              </div>

              {/* Task Control */}
              <div className="card">
                <h3 className="text-lg font-semibold text-workshop-100 mb-4">Task Control</h3>
                
                {selectedAgent.status === 'idle' ? (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-workshop-300 mb-2">
                        New Task
                      </label>
                      <textarea
                        value={taskInput}
                        onChange={(e) => setTaskInput(e.target.value)}
                        placeholder="Enter task description..."
                        className="input w-full h-24 resize-none"
                      />
                    </div>
                    <button
                      onClick={() => startTask(selectedAgent.name)}
                      disabled={!taskInput.trim()}
                      className="btn-primary disabled:opacity-50"
                    >
                      <Play className="w-4 h-4 mr-2" />
                      Start Task
                    </button>
                  </div>
                ) : selectedAgent.status === 'running' ? (
                  <div className="space-y-4">
                    <div className="flex items-center gap-2 text-sm text-workshop-400">
                      <Activity className="w-4 h-4 animate-pulse" />
                      <span>Agent is currently executing a task...</span>
                    </div>
                    <button
                      onClick={() => completeTask(selectedAgent.name)}
                      className="btn-secondary"
                    >
                      <CheckCircle className="w-4 h-4 mr-2" />
                      Mark Complete
                    </button>
                  </div>
                ) : selectedAgent.status === 'error' ? (
                  <div className="space-y-4">
                    <div className="flex items-center gap-2 text-sm text-status-error">
                      <AlertTriangle className="w-4 h-4" />
                      <span>Agent encountered an error</span>
                    </div>
                    <button
                      onClick={() => startTask(selectedAgent.name)}
                      className="btn-primary"
                    >
                      <RefreshCw className="w-4 h-4 mr-2" />
                      Retry Task
                    </button>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <CheckCircle className="w-8 h-8 text-status-ok mx-auto mb-2" />
                    <p className="text-workshop-500">Task completed successfully</p>
                  </div>
                )}
              </div>

              {/* Performance Metrics */}
              <div className="card">
                <h3 className="text-lg font-semibold text-workshop-100 mb-4">Performance</h3>
                <div className="diagnostic-grid">
                  <div className="metric-card">
                    <div className="metric-value">{selectedAgent.taskCount}</div>
                    <div className="metric-label">Total Tasks</div>
                  </div>
                  <div className="metric-card">
                    <div className="metric-value text-status-ok">{selectedAgent.successCount}</div>
                    <div className="metric-label">Successful</div>
                  </div>
                  <div className="metric-card">
                    <div className="metric-value text-status-error">{selectedAgent.errorCount}</div>
                    <div className="metric-label">Failed</div>
                  </div>
                  <div className="metric-card">
                    <div className="metric-value">
                      {selectedAgent.taskCount > 0 
                        ? ((selectedAgent.successCount / selectedAgent.taskCount) * 100).toFixed(1)
                        : '0'}%
                    </div>
                    <div className="metric-label">Success Rate</div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="card text-center py-12">
              <Users className="w-12 h-12 text-workshop-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-workshop-100 mb-2">
                No Agent Selected
              </h3>
              <p className="text-workshop-500">
                Select an agent from the list to view details and control tasks
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}