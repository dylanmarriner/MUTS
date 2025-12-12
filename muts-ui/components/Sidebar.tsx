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
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'ECU Management', href: '/ecu', icon: Cpu },
  { name: 'Diagnostics', href: '/diagnostics', icon: Activity },
  { name: 'Tuning', href: '/tuning', icon: Settings },
  { name: 'Security', href: '/security', icon: Shield },
  { name: 'Flashing', href: '/flashing', icon: Zap },
  { name: 'Logs', href: '/logs', icon: FileText },
  { name: 'Torque Advisory', href: '/torque', icon: TrendingUp },
  { name: 'SWAS', href: '/swas', icon: Circle },
  { name: 'Agents', href: '/agents', icon: Users },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="w-64 bg-workshop-900 border-r border-workshop-800 h-screen flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-workshop-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-mazda-600 rounded-lg flex items-center justify-center">
            <Zap className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-workshop-100">MUTS</h1>
            <p className="text-xs text-workshop-500">Technician Interface</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`sidebar-item ${isActive ? 'sidebar-item-active' : ''}`}
            >
              <item.icon className="w-5 h-5" />
              <span className="font-medium">{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-workshop-800">
        <div className="text-xs text-workshop-500 space-y-1">
          <p>Mazda Universal Tuning System</p>
          <p>v1.0.0 Production</p>
        </div>
      </div>
    </div>
  );
}