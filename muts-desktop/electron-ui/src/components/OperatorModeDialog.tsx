/**
 * Operator Mode Selection Dialog
 * Prompts user to select operator mode on startup
 */

import React, { useState, useEffect } from 'react';
import { AlertTriangle, Settings, Beaker } from 'lucide-react';

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

interface OperatorModeDialogProps {
  onSelect: (mode: 'dev' | 'workshop' | 'lab') => void;
  currentMode?: string;
}

const OperatorModeDialog: React.FC<OperatorModeDialogProps> = ({ 
  onSelect, 
  currentMode = 'dev' 
}) => {
  const [selectedMode, setSelectedMode] = useState<'dev' | 'workshop' | 'lab'>(currentMode as any);
  const [confirmed, setConfirmed] = useState(false);

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

  const handleConfirm = () => {
    if (selectedMode === 'workshop' || selectedMode === 'lab') {
      setConfirmed(true);
    } else {
      onSelect(selectedMode);
    }
  };

  const handleFinalConfirm = () => {
    onSelect(selectedMode);
  };

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
      <div className="bg-gray-900 rounded-lg border border-gray-700 p-8 max-w-2xl w-full mx-4">
        <h2 className="text-2xl font-bold text-white mb-2">Select Operator Mode</h2>
        <p className="text-gray-400 mb-6">
          Choose the appropriate mode for your use case. This determines system capabilities and safety features.
        </p>

        <div className="space-y-4 mb-6">
          {modes.map((mode) => {
            const Icon = mode.icon;
            const isSelected = selectedMode === mode.mode;
            
            return (
              <div
                key={mode.mode}
                onClick={() => setSelectedMode(mode.mode)}
                className={`
                  relative p-4 rounded-lg border-2 cursor-pointer transition-all
                  ${isSelected 
                    ? `${mode.bgColor} ${mode.borderColor} ${mode.color}` 
                    : 'bg-gray-800 border-gray-700 hover:border-gray-600'
                  }
                `}
              >
                <div className="flex items-start gap-3">
                  <Icon className={`w-6 h-6 mt-1 ${isSelected ? mode.color : 'text-gray-400'}`} />
                  <div className="flex-1">
                    <h3 className={`font-semibold mb-1 ${isSelected ? mode.color : 'text-white'}`}>
                      {mode.title}
                    </h3>
                    <p className={`text-sm ${isSelected ? 'text-gray-200' : 'text-gray-400'}`}>
                      {mode.description}
                    </p>
                    {mode.warning && isSelected && (
                      <div className={`mt-2 text-sm ${mode.color} font-medium`}>
                        ⚠️ {mode.warning}
                      </div>
                    )}
                  </div>
                  {isSelected && (
                    <div className={`w-5 h-5 rounded-full border-2 ${mode.borderColor} flex items-center justify-center`}>
                      <div className={`w-2.5 h-2.5 rounded-full ${mode.color.replace('text', 'bg')}`} />
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {!confirmed ? (
          <div className="flex justify-end gap-3">
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              disabled={selectedMode === null}
              className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Continue
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="bg-yellow-900/20 border border-yellow-700 rounded-lg p-4">
              <h3 className="text-yellow-400 font-semibold mb-2">Confirmation Required</h3>
              <p className="text-yellow-200 text-sm">
                You are about to start MUTS in {modes.find(m => m.mode === selectedMode)?.title}. 
                {selectedMode === 'workshop' && ' This will enable ECU write operations and requires real hardware.'}
                {selectedMode === 'lab' && ' This mode bypasses many safety features and should only be used for research.'}
              </p>
            </div>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setConfirmed(false)}
                className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
              >
                Back
              </button>
              <button
                onClick={handleFinalConfirm}
                className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Confirm & Start
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default OperatorModeDialog;
