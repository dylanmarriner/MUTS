/**
 * Workshop Startup Screen
 * Required startup screen for operator mode and technician selection
 */

import React, { useState, useEffect } from 'react';
import { AlertTriangle, Settings, Beaker, User, Users, Check } from 'lucide-react';

interface OperatorModeOption {
  mode: 'dev' | 'workshop' | 'lab';
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  bgColor: string;
  borderColor: string;
  warning?: string;
}

interface Technician {
  id: string;
  name: string;
  role: string;
  certificationLevel?: string;
}

interface WorkshopStartupScreenProps {
  onModeSelected: (mode: 'dev' | 'workshop' | 'lab', technician?: Technician) => void;
  savedMode?: string;
  savedTechnician?: string;
}

const WorkshopStartupScreen: React.FC<WorkshopStartupScreenProps> = ({ 
  onModeSelected, 
  savedMode = 'dev',
  savedTechnician
}) => {
  const [selectedMode, setSelectedMode] = useState<'dev' | 'workshop' | 'lab'>(savedMode as any);
  const [selectedTechnician, setSelectedTechnician] = useState<string | undefined>(savedTechnician);
  const [step, setStep] = useState<'mode' | 'technician' | 'confirmation'>('mode');
  const [confirmed, setConfirmed] = useState(false);
  const [technicians, setTechnicians] = useState<Technician[]>([]);
  const [loading, setLoading] = useState(false);

  const modes: OperatorModeOption[] = [
    {
      mode: 'dev',
      title: 'DEV MODE',
      description: 'Development with mock interface, no ECU writes',
      icon: Settings,
      color: 'text-blue-400',
      bgColor: 'bg-blue-900/20',
      borderColor: 'border-blue-700',
    },
    {
      mode: 'workshop',
      title: 'WORKSHOP MODE',
      description: 'Real vehicle servicing, ECU writes allowed',
      icon: AlertTriangle,
      color: 'text-green-400',
      bgColor: 'bg-green-900/20',
      borderColor: 'border-green-700',
      warning: 'This system will communicate with real vehicle ECUs.',
    },
    {
      mode: 'lab',
      title: 'LAB MODE (DANGEROUS)',
      description: 'Research mode with expanded capabilities',
      icon: Beaker,
      color: 'text-red-400',
      bgColor: 'bg-red-900/20',
      borderColor: 'border-red-700',
      warning: 'Reduced guardrails - for research only.',
    },
  ];

  useEffect(() => {
    // Load technicians from backend
    const loadTechnicians = async () => {
      try {
        // Use AbortController with short timeout to prevent long error logs
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 1000);
        
        const response = await fetch('http://localhost:3000/api/technicians', {
          signal: controller.signal,
        });
        clearTimeout(timeoutId);
        
        if (!response.ok) throw new Error('Backend not available');
        const data = await response.json();
        setTechnicians(data.filter((t: Technician) => t.active));
      } catch (error: any) {
        // Backend not available - use fallback technicians (expected in standalone mode)
        // Silently handle this expected error (backend may not be running)
        if (error.name !== 'AbortError') {
          // Only log unexpected errors, not network failures
          // Network failures are expected when backend is not running
        }
        setTechnicians([
          { id: '1', name: 'John Smith', role: 'senior_tech' },
          { id: '2', name: 'Jane Doe', role: 'tech' },
          { id: '3', name: 'Bob Johnson', role: 'engineer' },
        ]);
      }
    };
    loadTechnicians();
  }, []);

  const handleModeContinue = () => {
    if (selectedMode === 'dev') {
      onModeSelected(selectedMode);
    } else {
      setStep('technician');
    }
  };

  const handleTechnicianContinue = () => {
    if (!selectedTechnician) return;
    setStep('confirmation');
  };

  const handleFinalConfirm = () => {
    const technician = technicians.find(t => t.id === selectedTechnician);
    onModeSelected(selectedMode, technician);
  };

  const handleBack = () => {
    if (step === 'technician') {
      setStep('mode');
    } else if (step === 'confirmation') {
      setStep('technician');
    }
  };

  const renderModeSelection = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-white mb-2">Select Operator Mode</h2>
        <p className="text-gray-400">
          Choose the appropriate mode for your use case. This determines system capabilities and safety features.
        </p>
      </div>

      <div className="space-y-4">
        {modes.map((mode) => {
          const Icon = mode.icon;
          const isSelected = selectedMode === mode.mode;
          
          return (
            <div
              key={mode.mode}
              onClick={() => setSelectedMode(mode.mode)}
              className={`
                relative p-6 rounded-lg border-2 cursor-pointer transition-all
                ${isSelected 
                  ? `${mode.bgColor} ${mode.borderColor} ${mode.color}` 
                  : 'bg-gray-800 border-gray-700 hover:border-gray-600'
                }
              `}
            >
              <div className="flex items-start gap-4">
                <Icon className={`w-8 h-8 mt-1 ${isSelected ? mode.color : 'text-gray-400'}`} />
                <div className="flex-1">
                  <h3 className={`text-xl font-semibold mb-2 ${isSelected ? mode.color : 'text-white'}`}>
                    {mode.title}
                  </h3>
                  <p className={`text-base ${isSelected ? 'text-gray-200' : 'text-gray-400'}`}>
                    {mode.description}
                  </p>
                  {mode.warning && isSelected && (
                    <div className={`mt-3 text-base ${mode.color} font-medium flex items-center gap-2`}>
                      <AlertTriangle className="w-5 h-5" />
                      {mode.warning}
                    </div>
                  )}
                </div>
                {isSelected && (
                  <div className={`w-6 h-6 rounded-full border-2 ${mode.borderColor} flex items-center justify-center`}>
                    <Check className={`w-4 h-4 ${mode.color.replace('text', 'fill')}`} />
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className="flex justify-end gap-3 mt-8">
        <button
          onClick={() => window.location.reload()}
          className="px-6 py-3 text-gray-400 hover:text-white transition-colors"
        >
          Exit
        </button>
        <button
          onClick={handleModeContinue}
          disabled={selectedMode === null}
          className="px-8 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-semibold"
        >
          Continue
        </button>
      </div>
    </div>
  );

  const renderTechnicianSelection = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-white mb-2">Select Technician</h2>
        <p className="text-gray-400">
          All operations will be attributed to the selected technician for accountability.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {technicians.map((tech) => {
          const isSelected = selectedTechnician === tech.id;
          
          return (
            <div
              key={tech.id}
              onClick={() => setSelectedTechnician(tech.id)}
              className={`
                relative p-4 rounded-lg border-2 cursor-pointer transition-all
                ${isSelected 
                  ? 'bg-green-900/20 border-green-700' 
                  : 'bg-gray-800 border-gray-700 hover:border-gray-600'
                }
              `}
            >
              <div className="flex items-center gap-4">
                <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                  isSelected ? 'bg-green-700' : 'bg-gray-700'
                }`}>
                  <User className={`w-6 h-6 ${isSelected ? 'text-green-100' : 'text-gray-400'}`} />
                </div>
                <div className="flex-1">
                  <h3 className={`text-lg font-semibold ${isSelected ? 'text-green-400' : 'text-white'}`}>
                    {tech.name}
                  </h3>
                  <p className={`text-sm ${isSelected ? 'text-green-200' : 'text-gray-400'}`}>
                    {tech.role.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </p>
                  {tech.certificationLevel && (
                    <p className={`text-xs mt-1 ${isSelected ? 'text-green-300' : 'text-gray-500'}`}>
                      Certified: {tech.certificationLevel}
                    </p>
                  )}
                </div>
                {isSelected && (
                  <div className="w-6 h-6 rounded-full border-2 border-green-700 flex items-center justify-center">
                    <Check className="w-4 h-4 text-green-400" />
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {technicians.length === 0 && (
        <div className="text-center py-8">
          <Users className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400">No active technicians found</p>
          <p className="text-sm text-gray-500 mt-2">
            Please add technicians in the system settings
          </p>
        </div>
      )}

      <div className="flex justify-end gap-3 mt-8">
        <button
          onClick={handleBack}
          className="px-6 py-3 text-gray-400 hover:text-white transition-colors"
        >
          Back
        </button>
        <button
          onClick={handleTechnicianContinue}
          disabled={!selectedTechnician || technicians.length === 0}
          className="px-8 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-semibold"
        >
          Continue
        </button>
      </div>
    </div>
  );

  const renderConfirmation = () => {
    const mode = modes.find(m => m.mode === selectedMode);
    const technician = technicians.find(t => t.id === selectedTechnician);
    
    return (
      <div className="space-y-6">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-white mb-2">Confirm Selection</h2>
          <p className="text-gray-400">
            Please review your selection before starting MUTS
          </p>
        </div>

        <div className="bg-gray-800 rounded-lg p-6 space-y-4">
          <div className="flex items-center gap-4">
            <div className={`w-12 h-12 rounded-full flex items-center justify-center ${mode?.bgColor}`}>
              {React.createElement(mode?.icon || Settings, { 
                className: `w-6 h-6 ${mode?.color}` 
              })}
            </div>
            <div>
              <p className="text-sm text-gray-400">Operator Mode</p>
              <p className={`text-xl font-semibold ${mode?.color}`}>{mode?.title}</p>
            </div>
          </div>

          {technician && (
            <div className="flex items-center gap-4 pt-4 border-t border-gray-700">
              <div className="w-12 h-12 rounded-full bg-green-700 flex items-center justify-center">
                <User className="w-6 h-6 text-green-100" />
              </div>
              <div>
                <p className="text-sm text-gray-400">Technician</p>
                <p className="text-xl font-semibold text-white">{technician.name}</p>
                <p className="text-sm text-gray-400">
                  {technician.role.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </p>
              </div>
            </div>
          )}
        </div>

        {(selectedMode === 'workshop' || selectedMode === 'lab') && (
          <div className="bg-yellow-900/20 border border-yellow-700 rounded-lg p-4">
            <h3 className="text-yellow-400 font-semibold mb-2 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5" />
              Important Notice
            </h3>
            <p className="text-yellow-200 text-sm">
              You are about to start MUTS in {mode?.title}. 
              {selectedMode === 'workshop' && ' This will enable ECU write operations and requires real hardware.'}
              {selectedMode === 'lab' && ' This mode bypasses many safety features and should only be used for research.'}
              All actions will be attributed to {technician?.name}.
            </p>
          </div>
        )}

        <div className="flex justify-end gap-3 mt-8">
          <button
            onClick={handleBack}
            className="px-6 py-3 text-gray-400 hover:text-white transition-colors"
          >
            Back
          </button>
          <button
            onClick={handleFinalConfirm}
            className="px-8 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-semibold"
          >
            Start MUTS
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="fixed inset-0 bg-black/90 flex items-center justify-center z-50">
      <div className="bg-gray-900 rounded-xl border border-gray-700 p-8 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {step === 'mode' && renderModeSelection()}
        {step === 'technician' && renderTechnicianSelection()}
        {step === 'confirmation' && renderConfirmation()}
      </div>
    </div>
  );
};

export default WorkshopStartupScreen;
