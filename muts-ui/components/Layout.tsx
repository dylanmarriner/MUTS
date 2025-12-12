'use client';

import React from 'react';
import Sidebar from './Sidebar';
import HardwareStatus from './HardwareStatus';

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-workshop-950 flex">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <HardwareStatus />
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
}