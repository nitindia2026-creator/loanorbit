import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldCheck, ArrowRight, Lock, User, AlertCircle } from 'lucide-react';
import { api, setAuthToken } from '../lib/api';

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('superadmin');
  const [password, setPassword] = useState('AdminPass123!');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const data = await api.login({ username, password });
      setAuthToken(data.access_token, data.role, username);
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Login failed. Please check credentials.');
    } finally {
      setLoading(false);
    }
  };

  const setDemoRole = (u: string) => {
    setUsername(u);
    setPassword('AdminPass123!');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-950 flex items-center justify-center p-6">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-2xl p-8 border border-slate-100">
        <div className="flex items-center space-x-3 mb-6">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-teal-500 to-cyan-400 flex items-center justify-center text-white shadow-lg shadow-teal-500/20">
            <ShieldCheck className="w-7 h-7" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">LOANORBIT</h1>
            <p className="text-xs text-teal-600 font-semibold tracking-wider">ADMIN OPERATIONS LOGIN</p>
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5 text-red-500" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Admin Username
            </label>
            <div className="relative">
              <User className="w-5 h-5 absolute left-3.5 top-3 text-slate-400" />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="w-full pl-11 pr-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500 font-medium text-slate-800"
                placeholder="e.g. superadmin"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Password
            </label>
            <div className="relative">
              <Lock className="w-5 h-5 absolute left-3.5 top-3 text-slate-400" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full pl-11 pr-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500 font-medium text-slate-800"
                placeholder="••••••••••••"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-teal-600 to-cyan-600 text-white font-semibold flex items-center justify-center space-x-2 shadow-lg shadow-teal-600/25 hover:from-teal-700 hover:to-cyan-700 transition-all disabled:opacity-60"
          >
            <span>{loading ? 'Authenticating...' : 'Sign In to Portal'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        {/* Quick Demo Credentials */}
        <div className="mt-8 pt-6 border-t border-slate-100">
          <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3 text-center">
            Quick Fill Demo Roles
          </p>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <button
              onClick={() => setDemoRole('superadmin')}
              className="px-2.5 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium text-left truncate"
            >
              👑 Super Admin
            </button>
            <button
              onClick={() => setDemoRole('underwriter_lead')}
              className="px-2.5 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium text-left truncate"
            >
              📑 Underwriter
            </button>
            <button
              onClick={() => setDemoRole('kyc_lead')}
              className="px-2.5 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium text-left truncate"
            >
              🔍 KYC Officer
            </button>
            <button
              onClick={() => setDemoRole('finance_lead')}
              className="px-2.5 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium text-left truncate"
            >
              💰 Finance Officer
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
