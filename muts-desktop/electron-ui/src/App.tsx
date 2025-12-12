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
  const location = useLocation();
  const navigate = useNavigate();
  const [showStartup, setShowStartup] = useState(true);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [configLoaded, setConfigLoaded] = useState(false);

  // Load initial config
  useEffect(() => {
    console.log('App: Loading initial config');
    
    const loadConfig = async () => {
      try {
        console.log('App: Calling config.load()');
        const config = await window.electronAPI.config.load();
        console.log('App: Config loaded:', config);
        
        // Check if mode selection is required
        if (config.requireModeSelection) {
          console.log('App: Mode selection required');
          setShowStartup(true);
        } else {
          console.log('App: Mode selection not required');
          setShowStartup(false);
        }
      } catch (error) {
        console.error('App: Failed to load config:', error);
        setShowStartup(true);
      }
      setConfigLoaded(true);
    };
    
    loadConfig();
  }, []);

  // Initialize connection status on mount
  useEffect(() => {
    console.log('App: Initializing connection status');
    
    const initializeApp = async () => {
      try {
        console.log('App: Getting available interfaces');
        // Get available interfaces
        const interfaces = await window.electronAPI.interface.list();
        console.log('App: Interfaces:', interfaces);
        
        // Get current connection status
        const status = await window.electronAPI.interface.getStatus();
        console.log('App: Connection status:', status);
      } catch (error) {
        console.error('App: Failed to initialize app:', error);
      }
    };
    
    initializeApp();
  }, []);

  // Hide boot screen when app is ready
  useEffect(() => {
    if (!showStartup) {
      console.log('App: Hiding boot screen - app is ready');
      window.hideBootScreen();
    }
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
      console.log('App: Menu action:', action);
      
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
    console.log('App: Mode selected:', mode, selectedTechnician);
    
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
    console.log('App: Showing startup screen');
    return <WorkshopStartupScreen onModeSelected={handleModeSelected} />;
  }

  console.log('App: Rendering main app with tabs');
  
  return (
    <div className="h-screen flex flex-col bg-gray-900 text-white">
      {/* Header with navigation */}
      <header className="bg-gray-800 border-b border-gray-700 px-4 py-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <h1 className="text-lg font-bold">MUTS - Mazda Universal Tuning System</h1>
            <nav className="flex gap-1">
              {tabs.map((tab) => {
                const isActive = location.pathname === tab.path;
                return (
                  <button
                    key={tab.id}
                    onClick={() => navigate(tab.path)}
                    className={`flex items-center gap-2 px-3 py-1 rounded text-sm transition-colors ${
                      isActive 
                        ? 'bg-blue-600 text-white' 
                        : 'text-gray-400 hover:text-white hover:bg-gray-700'
                    }`}
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
              status="error" 
              label="Not Connected" 
            />
            <StatusIndicator 
              status="warning" 
              label="Safety Disarmed" 
            />
            <span className="text-xs text-gray-400">
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