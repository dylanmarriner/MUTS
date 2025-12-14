'use client';

import React from 'react';
import Sidebar from './Sidebar';
import HardwareStatus from './HardwareStatus';

interface LayoutProps {
  children: React.ReactNode;
  activeModule?: string;
  onModuleChange?: (module: string) => void;
}

export default function Layout({ children, activeModule = 'dashboard', onModuleChange }: LayoutProps) {
  return (
    <div className="min-h-screen bg-bg-primary flex scanlines">
      <Sidebar activeModule={activeModule} onModuleChange={onModuleChange} />
      <div className="flex-1 flex flex-col">
        <HardwareStatus />
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
}