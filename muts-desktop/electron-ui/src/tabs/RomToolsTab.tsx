/**
 * ROM Tools Tab
 * ROM analysis, editing, and validation tools
 */

import React, { useEffect, useState } from 'react';
import { Database, Upload, Download, Search, FileText, CheckCircle, AlertTriangle } from 'lucide-react';
import { useConnectionState } from '../stores/useAppStore';

interface RomInfo {
  fileName: string;
  fileSize: number;
  checksum: string;
  ecuType: string;
  calibrationId: string;
  version: string;
  isValid: boolean;
}

const RomToolsTab: React.FC = () => {
  const { isConnected, isDisconnected } = useConnectionState();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [romInfo, setRomInfo] = useState<RomInfo | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setRomInfo(null);
    }
  };

  const validateRom = async () => {
    if (!selectedFile) return;
    
    setIsValidating(true);
    try {
      const buffer = await selectedFile.arrayBuffer();
      const romData = new Uint8Array(buffer);
      
      const validation = await window.electronAPI.flash.validate(romData);
      const checksum = await window.electronAPI.flash.checksum(romData);
      
      setRomInfo({
        fileName: selectedFile.name,
        fileSize: selectedFile.size,
        checksum: checksum.calculated.toString(16),
        ecuType: validation.ecuType || 'Unknown',
        calibrationId: validation.calibrationId || 'Unknown',
        version: '1.0',
        isValid: validation.isValid,
      });
    } catch (error) {
      console.error('Failed to validate ROM:', error);
    } finally {
      setIsValidating(false);
    }
  };

  if (isDisconnected) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <Database size={64} className="mx-auto text-gray-600 mb-4" />
          <h2 className="text-xl font-semibold text-gray-400 mb-2">NO_INTERFACE_CONNECTED</h2>
          <p className="text-gray-500">Connect to an interface to use ROM tools</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 p-6 overflow-auto">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
          <Database size={24} />
          ROM Tools
        </h1>

        {/* File Upload */}
        <div className="bg-gray-900 rounded-lg p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Load ROM File</h2>
          <div className="border-2 border-dashed border-gray-700 rounded-lg p-8 text-center">
            <Upload size={48} className="mx-auto text-gray-500 mb-4" />
            <input
              type="file"
              accept=".bin,.hex,.rom"
              onChange={handleFileSelect}
              className="hidden"
              id="rom-file-input"
            />
            <label
              htmlFor="rom-file-input"
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
          
          {selectedFile && (
            <button
              onClick={validateRom}
              disabled={isValidating}
              className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 rounded-lg transition-colors flex items-center gap-2"
            >
              {isValidating ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
              ) : (
                <Search size={16} />
              )}
              Validate ROM
            </button>
          )}
        </div>

        {/* ROM Information */}
        {romInfo && (
          <div className="bg-gray-900 rounded-lg p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">ROM Information</h2>
              <div className={`flex items-center gap-2 ${
                romInfo.isValid ? 'text-green-400' : 'text-red-400'
              }`}>
                {romInfo.isValid ? <CheckCircle size={20} /> : <AlertTriangle size={20} />}
                <span className="font-medium">
                  {romInfo.isValid ? 'Valid ROM' : 'Invalid ROM'}
                </span>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-gray-400">File Name:</span>
                <p className="font-medium">{romInfo.fileName}</p>
              </div>
              <div>
                <span className="text-gray-400">File Size:</span>
                <p className="font-medium">{(romInfo.fileSize / 1024 / 1024).toFixed(2)} MB</p>
              </div>
              <div>
                <span className="text-gray-400">Checksum:</span>
                <p className="font-mono text-sm">{romInfo.checksum}</p>
              </div>
              <div>
                <span className="text-gray-400">ECU Type:</span>
                <p className="font-medium">{romInfo.ecuType}</p>
              </div>
              <div>
                <span className="text-gray-400">Calibration ID:</span>
                <p className="font-mono text-sm">{romInfo.calibrationId}</p>
              </div>
              <div>
                <span className="text-gray-400">Version:</span>
                <p className="font-medium">{romInfo.version}</p>
              </div>
            </div>
          </div>
        )}

        {/* ROM Tools */}
        <div className="grid grid-cols-2 gap-6 mb-6">
          <div className="bg-gray-900 rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4">Analysis Tools</h2>
            <div className="space-y-3">
              <button className="w-full p-3 bg-gray-800 hover:bg-gray-700 rounded-lg text-left transition-colors">
                <h3 className="font-medium mb-1">Find Maps</h3>
                <p className="text-sm text-gray-400">Locate and identify tuning maps</p>
              </button>
              
              <button className="w-full p-3 bg-gray-800 hover:bg-gray-700 rounded-lg text-left transition-colors">
                <h3 className="font-medium mb-1">Compare ROMs</h3>
                <p className="text-sm text-gray-400">Compare two ROM files</p>
              </button>
              
              <button className="w-full p-3 bg-gray-800 hover:bg-gray-700 rounded-lg text-left transition-colors">
                <h3 className="font-medium mb-1">Extract Tables</h3>
                <p className="text-sm text-gray-400">Extract all tables to CSV</p>
              </button>
              
              <button className="w-full p-3 bg-gray-800 hover:bg-gray-700 rounded-lg text-left transition-colors">
                <h3 className="font-medium mb-1">Checksum Analysis</h3>
                <p className="text-sm text-gray-400">Analyze and verify checksums</p>
              </button>
            </div>
          </div>

          <div className="bg-gray-900 rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4">Editing Tools</h2>
            <div className="space-y-3">
              <button className="w-full p-3 bg-gray-800 hover:bg-gray-700 rounded-lg text-left transition-colors">
                <h3 className="font-medium mb-1">Hex Editor</h3>
                <p className="text-sm text-gray-400">Open in hex editor</p>
              </button>
              
              <button className="w-full p-3 bg-gray-800 hover:bg-gray-700 rounded-lg text-left transition-colors">
                <h3 className="font-medium mb-1">Patch Generator</h3>
                <p className="text-sm text-gray-400">Create patch file</p>
              </button>
              
              <button className="w-full p-3 bg-gray-800 hover:bg-gray-700 rounded-lg text-left transition-colors">
                <h3 className="font-medium mb-1">Definition Editor</h3>
                <p className="text-sm text-gray-400">Edit map definitions</p>
              </button>
              
              <button className="w-full p-3 bg-gray-800 hover:bg-gray-700 rounded-lg text-left transition-colors">
                <h3 className="font-medium mb-1">Batch Operations</h3>
                <p className="text-sm text-gray-400">Apply batch changes</p>
              </button>
            </div>
          </div>
        </div>

        {/* Recent Files */}
        <div className="bg-gray-900 rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <FileText size={20} />
            Recent ROM Files
          </h2>
          
          <div className="space-y-2">
            <div className="p-3 bg-gray-800 rounded-lg flex items-center justify-between">
              <div>
                <div className="font-medium">speed3_stock.bin</div>
                <div className="text-sm text-gray-400">2.0 MB • Modified 2 hours ago</div>
              </div>
              <button className="p-2 hover:bg-gray-700 rounded-lg transition-colors">
                <Download size={16} />
              </button>
            </div>
            
            <div className="p-3 bg-gray-800 rounded-lg flex items-center justify-between">
              <div>
                <div className="font-medium">speed3_stage1.bin</div>
                <div className="text-sm text-gray-400">2.0 MB • Modified yesterday</div>
              </div>
              <button className="p-2 hover:bg-gray-700 rounded-lg transition-colors">
                <Download size={16} />
              </button>
            </div>
            
            <div className="p-3 bg-gray-800 rounded-lg flex items-center justify-between">
              <div>
                <div className="font-medium">speed3_e85.bin</div>
                <div className="text-sm text-gray-400">2.0 MB • Modified 3 days ago</div>
              </div>
              <button className="p-2 hover:bg-gray-700 rounded-lg transition-colors">
                <Download size={16} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RomToolsTab;
