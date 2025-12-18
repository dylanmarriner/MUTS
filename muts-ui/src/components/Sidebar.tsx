'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  Cpu, 
  Activity, 
  Settings, 
  Shield, 
  Zap, 
  FileText, 
  TrendingUp, 
  Circle, 
  Users,
  Home
} from 'lucide-react';

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home, key: 'dashboard' },
  { name: 'ECU Management', href: '/ecu', icon: Cpu, key: 'ecu' },
  { name: 'Diagnostics', href: '/diagnostics', icon: Activity, key: 'diagnostics' },
  { name: 'Tuning', href: '/tuning', icon: Settings, key: 'tuning' },
  { name: 'Security', href: '/security', icon: Shield, key: 'security' },
  { name: 'Flashing', href: '/flashing', icon: Zap, key: 'flashing' },
  { name: 'Logs', href: '/logs', icon: FileText, key: 'logs' },
  { name: 'Torque Advisory', href: '/torque', icon: TrendingUp, key: 'torque' },
  { name: 'SWAS', href: '/swas', icon: Circle, key: 'swas' },
  { name: 'Agents', href: '/agents', icon: Users, key: 'agents' },
];

export default function Sidebar({ activeModule = 'dashboard', onModuleChange }: { 
  activeModule?: string; 
  onModuleChange?: (module: string) => void;
}) {
  return (
    <div className="w-64 bg-bg-panel backdrop-blur-holo border-r border-cyan-500/30 h-screen flex flex-col noise">
      {/* Logo */}
      <div className="p-6 border-b border-cyan-500/30">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-cyan-violet rounded-lg flex items-center justify-center shadow-glow-cyan">
            <Zap className="w-6 h-6 text-cyan-400" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-cyan-400 font-mono glitch">MUTS</h1>
            <p className="text-xs text-violet-400 font-mono">Technician Interface</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navigation.map((item) => {
          const isActive = activeModule === item.key;
          
          return (
            <button
              key={item.key}
              onClick={() => onModuleChange && onModuleChange(item.key)}
              className={`sidebar-item ${isActive ? 'sidebar-item-active' : ''} w-full text-left`}
            >
              <item.icon className="w-5 h-5" />
              <span className="font-medium">{item.name}</span>
            </button>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-cyan-500/30">
        <div className="text-xs text-text-muted font-mono space-y-1">
          <p>Mazda Universal Tuning System</p>
          <p className="text-cyan-400">v1.0.0 Production</p>
        </div>
      </div>
    </div>
  );
}