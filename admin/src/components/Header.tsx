import React from 'react';
import { AlertCircle, ShieldAlert } from 'lucide-react';

interface HeaderProps {
  title: string;
  subtitle?: string;
}

export const Header: React.FC<HeaderProps> = ({ title, subtitle }) => {
  return (
    <header className="bg-white border-b border-slate-200 px-8 py-5 flex items-center justify-between sticky top-0 z-10 shadow-sm">
      <div>
        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">{title}</h2>
        {subtitle && <p className="text-sm text-slate-500 mt-0.5">{subtitle}</p>}
      </div>

      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-2 bg-amber-50 border border-amber-200 text-amber-800 px-3.5 py-1.5 rounded-full text-xs font-semibold">
          <ShieldAlert className="w-4 h-4 text-amber-600" />
          <span>SYNTHETIC DEMO MODE</span>
        </div>
      </div>
    </header>
  );
};
