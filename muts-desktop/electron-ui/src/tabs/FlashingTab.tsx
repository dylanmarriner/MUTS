/**
 * Flashing Tab
 * ROM flashing operations with safety workflows
 */

import React, { useEffect, useState } from 'react';
import { Zap, Upload, AlertTriangle, CheckCircle, Clock, Play, Square } from 'lucide-react';
import { useConnectionState, useSafetyState, useAppStore } from '../stores/useAppStore';

interface FlashJob {
  id: string;
  status: 'pending' | 'preparing' | 'backup' | 'writing' | 'verifying' | 'complete' | 'failed' | 'aborted';
  progress: number;
  currentBlock: number;
  totalBlocks: number;
  stage: string;
  message: string;
  estimatedTime?: number;
}

const FlashingTab: React.FC = () => {
  const { isConnected, isDisconnected } = useConnectionState();
  const { canFlash, safetyArmed, safetyLevel } = useSafetyState();
  
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [flashJob, setFlashJob] = useState<FlashJob | null>(null);
  const [isPreparing, setIsPreparing] = useState(false);
  const [backupEnabled, setBackupEnabled] = useState(true);
  const [verifyEnabled, setVerifyEnabled] = useState(true);

  useEffect(() => {
    // Simulate flash job updates
    if (flashJob && flashJob.status === 'writing') {
      const interval = setInterval(() => {
        setFlashJob(prev => {
          if (!prev || prev.status !== 'writing') return prev;
          
          const newProgress = Math.min(prev.progress + 2, 100);
          const newBlock = Math.floor((newProgress / 100) * prev.totalBlocks);
          
          if (newProgress >= 100) {
            return {
              ...prev,
              status: 'complete',
              progress: 100,
              currentBlock: prev.totalBlocks,
              stage: 'complete',
              message: 'Flash completed successfully',
            };
          }
          
          return {
            ...prev,
            progress: newProgress,
            currentBlock: newBlock,
            message: `Writing block ${newBlock} of ${prev.totalBlocks}`,
          };
        });
      }, 100);
      
      return () => clearInterval(interval);
    }
  }, [flashJob]);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setFlashJob(null);
    }
  };

  const prepareFlash = async () => {
    if (!selectedFile) return;
    
    setIsPreparing(true);
    try {
      const buffer = await selectedFile.arrayBuffer();
      const romData = new Uint8Array(buffer);
      
      const result = await window.electronAPI.flash.prepare(
        romData,
        {
          verifyAfterWrite: verifyEnabled,
          backupBeforeFlash: backupEnabled,
          skipRegions: [],
        }
      );
      
      setFlashJob({
        id: result.jobId,
        status: 'pending',
        progress: 0,
        currentBlock: 0,
        totalBlocks: result.blocksToWrite,
        stage: 'pending',
        message: 'Ready to flash',
        estimatedTime: result.estimatedTimeSec,
      });
    } catch (error) {
      console.error('Failed to prepare flash:', error);
    } finally {
      setIsPreparing(false);
    }
  };

  const startFlashing = async () => {
    if (!flashJob) return;
    
    try {
      setFlashJob({ ...flashJob, status: 'writing', stage: 'writing', message: 'Starting flash...' });
      await window.electronAPI.flash.execute(flashJob.id);
    } catch (error) {
      console.error('Failed to start flash:', error);
      setFlashJob({ ...flashJob, status: 'failed', message: 'Flash failed' });
    }
  };

  const abortFlashing = async () => {
    if (!flashJob) return;
    
    try {
      await window.electronAPI.flash.abort(flashJob.id);
      setFlashJob({ ...flashJob, status: 'aborted', message: 'Flash aborted by user' });
    } catch (error) {
      console.error('Failed to abort flash:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'complete': return 'text-green-500';
      case 'failed': return 'text-red-500';
      case 'aborted': return 'text-yellow-500';
      case 'writing': return 'text-blue-500';
      default: return 'text-gray-500';
    }
  };

  if (isDisconnected) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <Zap size={64} className="mx-auto text-gray-600 mb-4" />
          <h2 className="text-xl font-semibold text-gray-400 mb-2">NO_INTERFACE_CONNECTED</h2>
          <p className="text-gray-500">Connect to an interface to use flashing features</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 p-6 overflow-auto">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
          <Zap size={24} />
          Flashing
        </h1>

        {/* Safety Warning */}
        {!canFlash && (
          <div className="bg-red-500/10 border border-red-500 rounded-lg p-4 mb-6 flex items-center gap-3">
            <AlertTriangle className="text-red-500" size={20} />
            <div>
              <p className="font-medium">Safety Requirements Not Met</p>
              <p className="text-sm text-gray-400">
                Safety system must be armed at Flash level to enable flashing
              </p>
            </div>
          </div>
        )}

        {/* File Selection */}
        <div className="bg-gray-900 rounded-lg p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Select ROM File</h2>
          <div className="border-2 border-dashed border-gray-700 rounded-lg p-8 text-center">
            <Upload size={48} className="mx-auto text-gray-500 mb-4" />
            <input
              type="file"
              accept=".bin,.hex,.rom"
              onChange={handleFileSelect}
              className="hidden"
              id="flash-file-input"
            />
            <label
              htmlFor="flash-file-input"
              className="cursor-pointer inline-block px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
            >
              Select ROM File
            </label>
            {selectedFile && (
              <p className="mt-4 text-sm text-gray-400">
                Selected: {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
              </p>
            )}
          </div>
        </div>

        {/* Flash Options */}
        {selectedFile && (
          <div className="bg-gray-900 rounded-lg p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4">Flash Options</h2>
            <div className="space-y-3">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={backupEnabled}
                  onChange={(e) => setBackupEnabled(e.target.checked)}
                  className="w-4 h-4 text-red-600 rounded"
                />
                <div>
                  <div className="font-medium">Create Backup</div>
                  <div className="text-sm text-gray-400">Backup current ROM before flashing</div>
                </div>
              </label>
              
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={verifyEnabled}
                  onChange={(e) => setVerifyEnabled(e.target.checked)}
                  className="w-4 h-4 text-red-600 rounded"
                />
                <div>
                  <div className="font-medium">Verify After Flash</div>
                  <div className="text-sm text-gray-400">Verify ROM integrity after flashing</div>
                </div>
              </label>
            </div>
            
            <button
              onClick={prepareFlash}
              disabled={isPreparing || !canFlash}
              className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 rounded-lg transition-colors flex items-center gap-2"
            >
              {isPreparing ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
              ) : (
                <Clock size={16} />
              )}
              {isPreparing ? 'Preparing...' : 'Prepare Flash'}
            </button>
          </div>
        )}

        {/* Flash Progress */}
        {flashJob && (
          <div className="bg-gray-900 rounded-lg p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Flash Progress</h2>
              <div className={`flex items-center gap-2 ${getStatusColor(flashJob.status)}`}>
                {flashJob.status === 'complete' && <CheckCircle size={20} />}
                {flashJob.status === 'failed' && <AlertTriangle size={20} />}
                {flashJob.status === 'aborted' && <AlertTriangle size={20} />}
                {flashJob.status === 'writing' && (
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500" />
                )}
                <span className="font-medium capitalize">{flashJob.status}</span>
              </div>
            </div>
            
            <div className="mb-4">
              <div className="flex justify-between text-sm mb-2">
                <span>Progress</span>
                <span>{flashJob.progress.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-800 rounded-full h-3">
                <div
                  className="bg-red-500 h-3 rounded-full transition-all duration-300"
                  style={{ width: `${flashJob.progress}%` }}
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-400">Current Block:</span>
                <p className="font-medium">{flashJob.currentBlock} / {flashJob.totalBlocks}</p>
              </div>
              <div>
                <span className="text-gray-400">Stage:</span>
                <p className="font-medium capitalize">{flashJob.stage}</p>
              </div>
              <div>
                <span className="text-gray-400">Job ID:</span>
                <p className="font-mono text-xs">{flashJob.id}</p>
              </div>
              {flashJob.estimatedTime && (
                <div>
                  <span className="text-gray-400">Est. Time:</span>
                  <p className="font-medium">{flashJob.estimatedTime}s</p>
                </div>
              )}
            </div>
            
            <div className="mt-4 p-3 bg-gray-800 rounded-lg">
              <p className="text-sm text-gray-400">{flashJob.message}</p>
            </div>
            
            <div className="mt-4 flex gap-2">
              {flashJob.status === 'pending' && (
                <button
                  onClick={startFlashing}
                  className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors flex items-center gap-2"
                >
                  <Play size={16} />
                  Start Flashing
                </button>
              )}
              
              {(flashJob.status === 'writing' || flashJob.status === 'pending') && (
                <button
                  onClick={abortFlashing}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors flex items-center gap-2"
                >
                  <Square size={16} />
                  Abort
                </button>
              )}
            </div>
          </div>
        )}

        {/* Flash History */}
        <div className="bg-gray-900 rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Flash History</h2>
          <div className="space-y-2">
            <div className="p-3 bg-gray-800 rounded-lg flex items-center justify-between">
              <div>
                <div className="font-medium">speed3_stage1.bin</div>
                <div className="text-sm text-gray-400">Completed 2 hours ago</div>
              </div>
              <div className="flex items-center gap-2 text-green-400">
                <CheckCircle size={16} />
                <span className="text-sm">Success</span>
              </div>
            </div>
            
            <div className="p-3 bg-gray-800 rounded-lg flex items-center justify-between">
              <div>
                <div className="font-medium">speed3_stock.bin</div>
                <div className="text-sm text-gray-400">Completed yesterday</div>
              </div>
              <div className="flex items-center gap-2 text-green-400">
                <CheckCircle size={16} />
                <span className="text-sm">Success</span>
              </div>
            </div>
            
            <div className="p-3 bg-gray-800 rounded-lg flex items-center justify-between">
              <div>
                <div className="font-medium">speed3_test.bin</div>
                <div className="text-sm text-gray-400">Failed 3 days ago</div>
              </div>
              <div className="flex items-center gap-2 text-red-400">
                <AlertTriangle size={16} />
                <span className="text-sm">Failed</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FlashingTab;
