import React, { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { HardwareProvider } from './contexts/HardwareContext';
import Layout from './components/Layout';
import ECUManagement from './components/ECUManagement';
import DiagnosticsInterface from './components/DiagnosticsInterface';
import TuningInterface from './components/TuningInterface';
import SecurityInterface from './components/SecurityInterface';
import FlashingInterface from './components/FlashingInterface';
import LogsInterface from './components/LogsInterface';
import TorqueInterface from './components/TorqueInterface';
import SWASInterface from './components/SWASInterface';
import AgentsInterface from './components/AgentsInterface';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5000,
      retry: 1,
    },
  },
});

// Component mapping for state-based navigation
const components = {
  dashboard: ECUManagement,
  ecu: ECUManagement,
  diagnostics: DiagnosticsInterface,
  tuning: TuningInterface,
  security: SecurityInterface,
  flashing: FlashingInterface,
  logs: LogsInterface,
  torque: TorqueInterface,
  swas: SWASInterface,
  agents: AgentsInterface,
};

function App() {
  const [activeModule, setActiveModule] = useState('dashboard');
  
  // Get the active component
  const ActiveComponent = components[activeModule] || components.dashboard;

  return (
    <QueryClientProvider client={queryClient}>
      <HardwareProvider>
        <div className="min-h-screen bg-workshop-950">
          <Layout activeModule={activeModule} onModuleChange={setActiveModule}>
            <ActiveComponent />
          </Layout>
        </div>
      </HardwareProvider>
    </QueryClientProvider>
  );
}

export default App;
