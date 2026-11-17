import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  FileCheck2,
  FileSpreadsheet,
  BookOpen,
  History,
  LogOut,
  ShieldCheck,
} from 'lucide-react';
import { clearAuthToken } from '../lib/api';

export const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const username = localStorage.getItem('loanorbit_admin_username') || 'Admin';
  const role = localStorage.getItem('loanorbit_admin_role') || 'SUPER_ADMIN';

  const handleLogout = () => {
    clearAuthToken();
    navigate('/login');
  };

  const navItems = [
    { to: '/', label: 'Overview', icon: LayoutDashboard },
    { to: '/customers', label: 'Customers', icon: Users },
    { to: '/kyc-queue', label: 'KYC Desk', icon: FileCheck2 },
    { to: '/underwriting', label: 'Underwriting', icon: FileSpreadsheet },
    { to: '/ledger', label: 'General Ledger', icon: BookOpen },
    { to: '/audit-logs', label: 'Security & Audit', icon: History },
  ];

  return (
    <aside className="w-64 bg-orbit-dark text-slate-300 flex flex-col shrink-0 min-h-screen border-r border-slate-800">
      {/* Brand Header */}
      <div className="p-6 border-b border-slate-800 flex items-center space-x-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-teal-500 to-cyan-400 flex items-center justify-center text-white shadow-lg shadow-teal-500/20">
          <ShieldCheck className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white">LOANORBIT</h1>
          <p className="text-xs text-teal-400 font-medium tracking-wide">OPS PLATFORM</p>
        </div>
      </div>

      {/* Nav Links */}
      <nav className="flex-1 p-4 space-y-1.5 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center space-x-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-teal-600/20 text-teal-400 border border-teal-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`
              }
            >
              <Icon className="w-5 h-5 shrink-0" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* User & Role Badge */}
      <div className="p-4 border-t border-slate-800 bg-slate-900/50">
        <div className="flex items-center justify-between mb-3">
          <div>
            <p className="text-sm font-semibold text-white truncate">{username}</p>
            <span className="inline-block px-2 py-0.5 mt-1 text-[10px] font-bold rounded-full bg-teal-500/10 text-teal-400 border border-teal-500/20">
              {role}
            </span>
          </div>
          <button
            onClick={handleLogout}
            title="Log out"
            className="p-2 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded-lg transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
        <p className="text-[11px] text-slate-500 text-center">
          SANDBOX DEMO ENVIRONMENT
        </p>
      </div>
    </aside>
  );
};
