/**
 * Main Application Component
 * Provides the shell layout with navigation, status bar, and tab content
 */

import React, { useEffect, useState } from 'react';
import { Routes, Route, useLocation, useNavigate } from 'react-router-dom';
import { 
  Car, 
  Plug, 
  Activity, 
  Radio, 
  Wrench, 
  Settings, 
  Database, 
  Zap, 
  FileText, 
  Shield,
  User
} from 'lucide-react';
import WorkshopStartupScreen from './components/WorkshopStartupScreen';
import { OperatorMode, Technician } from './types';
import { useAppStore, useConnectionState, useSafetyState } from './stores/useAppStore';

// Import tab components
import VehicleInfoTab from './tabs/VehicleInfoTab';
import ConnectTab from './tabs/ConnectTab';
import LiveDataTab from './tabs/LiveDataTab';
import StreamTab from './tabs/StreamTab';
import DiagnosticsTab from './tabs/DiagnosticsTab';
import TuningTab from './tabs/TuningTab';
import RomToolsTab from './tabs/RomToolsTab';
import FlashingTab from './tabs/FlashingTab';
import LogsTab from './tabs/LogsTab';
import SettingsTab from './tabs/SettingsTab';

// Tab configuration
const tabs = [
  { id: 'vehicle', label: 'Info / Vehicle', icon: Car, path: '/' },
  { id: 'connect', label: 'Connect / Interface', icon: Plug, path: '/connect' },
  { id: 'live-data', label: 'Live Data', icon: Activity, path: '/live-data' },
  { id: 'stream', label: 'Stream', icon: Radio, path: '/stream' },
  { id: 'diagnostics', label: 'Diagnostics', icon: Wrench, path: '/diagnostics' },
  { id: 'tuning', label: 'Tuning', icon: Settings, path: '/tuning' },
  { id: 'rom-tools', label: 'ROM Tools', icon: Database, path: '/rom-tools' },
  { id: 'flashing', label: 'Flashing', icon: Zap, path: '/flashing' },
  { id: 'logs', label: 'Logs / Timeline', icon: FileText, path: '/logs' },
  { id: 'settings', label: 'Settings / Safety', icon: Shield, path: '/settings' },
];

// Status indicator component
const StatusIndicator = ({ status, label }: { status: 'good' | 'warning' | 'error', label: string }) => {
  const colors = {
    good: 'bg-green-500',
    warning: 'bg-yellow-500',
    error: 'bg-red-500'
  };

  return (
    <div className="flex items-center gap-2">
      <div className={`w-2 h-2 rounded-full ${colors[status]}`} />
      <span className="text-xs">{label}</span>
    </div>
  );
};

function App() {
  console.log('=== App component rendering ===');
  
  const location = useLocation();
  const navigate = useNavigate();
  const { 
    operatorMode, 
    setOperatorMode, 
    technician, 
    setTechnician,
    showStartup,
    setShowStartup
  } = useAppStore();
  
  const connectionState = useConnectionState();
  const safetyState = useSafetyState();
  const [currentTime, setCurrentTime] = useState(new Date());
  const [currentSession, setCurrentSession] = useState<any>(null);

  // Get operator mode from Electron - run once
  useEffect(() => {
    const getOperatorMode = async () => {
      try {
        const mode = await window.electronAPI.getOperatorMode?.();
        if (mode) {
          setOperatorMode(mode as OperatorMode);
        }
      } catch (error) {
        console.error('App: Failed to get operator mode:', error);
      }
    };
    getOperatorMode();
  }, [setOperatorMode]);

  // Load initial config - run once
  useEffect(() => {
    const loadConfig = async () => {
      try {
        const config = await window.electronAPI.config.load();
        
        setOperatorMode(config.operatorMode);
        setTechnician(config.technicianId ? { id: config.technicianId } : null);
        
        // Report config loaded
        if (window.electronAPI.healthCheckpoint) {
          window.electronAPI.healthCheckpoint('CONFIG_LOADED', 'Configuration loaded', 'PASS', undefined, { operatorMode: config.operatorMode });
        }
        
        // Check if mode selection is required
        if (config.requireModeSelection) {
          setShowStartup(true);
        } else {
          setShowStartup(false);
        }
      } catch (error) {
        console.error('App: Failed to load config:', error);
        if (window.electronAPI.healthCheckpoint) {
          window.electronAPI.healthCheckpoint('CONFIG_LOADED', 'Configuration loaded', 'DEGRADED', error instanceof Error ? error.message : String(error));
        }
        setShowStartup(true);
      }
    };
    loadConfig();
  }, [setOperatorMode, setTechnician, setShowStartup]);

  // Initialize connection status on mount - run once
  useEffect(() => {
    const initializeApp = async () => {
      try {
        // Get available interfaces
        const interfaces = await window.electronAPI.interface.list();
        
        // Get current connection status
        const status = await window.electronAPI.interface.getStatus();
      } catch (error) {
        console.error('App: Failed to initialize app:', error);
      }
    };
    
    initializeApp();
  }, []);

  // Hide boot screen when app is ready
  useEffect(() => {
    // Always hide boot screen after a short delay to ensure React has rendered
    const timer = setTimeout(() => {
      if (window.hideBootScreen) {
        window.hideBootScreen();
      }
    }, 100);
    return () => clearTimeout(timer);
  }, [showStartup]);

  // Update time
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Handle menu actions from main process
  useEffect(() => {
    window.electronAPI.onMenuAction((action: string) => {
      switch (action) {
        case 'open-rom':
          navigate('/rom-tools');
          break;
        case 'save-profile':
          // TODO: Implement save profile
          break;
        case 'connect':
          navigate('/connect');
          break;
        case 'arm-safety':
          navigate('/settings');
          break;
      }
    });
  }, [navigate]);

  const handleModeSelected = (mode: OperatorMode, selectedTechnician?: Technician) => {
    setOperatorMode(mode);
    setTechnician(selectedTechnician || null);
    
    // Save mode and technician
    const saveMode = async () => {
      try {
        await window.electronAPI.config.setOperatorMode(mode);
        if (selectedTechnician) {
          await window.electronAPI.config.setTechnician(selectedTechnician.id);
        }
        await window.electronAPI.config.skipModeSelection(true);
        setShowStartup(false);
      } catch (error) {
        console.error('App: Failed to save mode:', error);
      }
    };
    
    saveMode();
  };

  // Show startup screen if needed
  if (showStartup) {
    return <WorkshopStartupScreen onModeSelected={handleModeSelected} />;
  }
  
  return (
    <div className="h-screen flex flex-col text-white relative" style={{ background: 'radial-gradient(ellipse at center, rgba(30, 41, 59, 1), rgba(0, 0, 0, 1))' }}>
      {/* Header with navigation - Dylan Sci-fi Theme */}
      <header className="px-4 py-2 relative z-10" style={{ 
        background: 'rgba(15, 23, 42, 0.9)',
        backdropFilter: 'blur(8px)',
        borderBottom: '1px solid rgba(6, 182, 212, 0.3)',
        boxShadow: '0 0 20px rgba(6, 182, 212, 0.1)'
      }}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <h1 className="text-lg font-bold" style={{ 
              background: 'linear-gradient(to right, rgba(6, 182, 212, 1), rgba(217, 70, 239, 1))',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}>
              MUTS - Mazda Universal Tuning System
            </h1>
            <nav className="flex gap-1">
              {tabs.map((tab) => {
                const isActive = location.pathname === tab.path;
                return (
                  <button
                    key={tab.id}
                    onClick={() => navigate(tab.path)}
                    className="flex items-center gap-2 px-3 py-1 rounded text-sm transition-all"
                    style={{
                      background: isActive 
                        ? 'rgba(6, 182, 212, 0.2)' 
                        : 'transparent',
                      border: isActive 
                        ? '1px solid rgba(6, 182, 212, 0.5)' 
                        : '1px solid transparent',
                      color: isActive 
                        ? 'rgba(6, 182, 212, 1)' 
                        : 'rgba(203, 213, 225, 1)',
                      boxShadow: isActive 
                        ? '0 0 10px rgba(6, 182, 212, 0.5)' 
                        : 'none'
                    }}
                    onMouseEnter={(e) => {
                      if (!isActive) {
                        e.currentTarget.style.background = 'rgba(6, 182, 212, 0.1)';
                        e.currentTarget.style.borderColor = 'rgba(6, 182, 212, 0.3)';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isActive) {
                        e.currentTarget.style.background = 'transparent';
                        e.currentTarget.style.borderColor = 'transparent';
                      }
                    }}
                  >
                    <tab.icon className="w-4 h-4" />
                    {tab.label}
                  </button>
                );
              })}
            </nav>
          </div>
          
          <div className="flex items-center gap-4">
            <StatusIndicator 
              status={connectionState.connected ? 'good' : 'error'} 
              label={connectionState.connected ? 'Connected' : 'Not Connected'} 
            />
            <StatusIndicator 
              status={safetyState.armed ? 'error' : 'warning'} 
              label={safetyState.armed ? 'Safety Armed' : 'Safety Disarmed'} 
            />
            {currentSession && (
              <span className="text-xs" style={{ color: 'rgba(148, 163, 184, 1)' }}>
                Session: {currentSession.id.substring(0, 8)}
              </span>
            )}
            <span className="text-xs font-mono" style={{ color: 'rgba(6, 182, 212, 1)' }}>
              {currentTime.toLocaleTimeString()}
            </span>
          </div>
        </div>
      </header>

      {/* Main content area */}
      <main className="flex-1 overflow-hidden">
        <Routes>
          <Route path="/" element={<VehicleInfoTab />} />
          <Route path="/connect" element={<ConnectTab />} />
          <Route path="/live-data" element={<LiveDataTab />} />
          <Route path="/stream" element={<StreamTab />} />
          <Route path="/diagnostics" element={<DiagnosticsTab />} />
          <Route path="/tuning" element={<TuningTab />} />
          <Route path="/rom-tools" element={<RomToolsTab />} />
          <Route path="/flashing" element={<FlashingTab />} />
          <Route path="/logs" element={<LogsTab />} />
          <Route path="/settings" element={<SettingsTab />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;