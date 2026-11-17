import React, { useEffect, useState } from 'react';
import {
  Users,
  FileSpreadsheet,
  AlertCircle,
  FileCheck2,
  DollarSign,
  TrendingUp,
  CreditCard,
  CheckCircle2,
} from 'lucide-react';
import { Header } from '../components/Header';
import { api } from '../lib/api';

export const Dashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getDashboard()
      .then((data) => setMetrics(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600"></div>
      </div>
    );
  }

  const formatCurrency = (paise: number = 0) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(paise / 100);
  };

  const statCards = [
    {
      label: 'Total Registered Customers',
      value: metrics?.total_customers || 0,
      icon: Users,
      color: 'text-blue-600',
      bg: 'bg-blue-50',
    },
    {
      label: 'Applications Pending Review',
      value: metrics?.pending_applications || 0,
      icon: FileSpreadsheet,
      color: 'text-amber-600',
      bg: 'bg-amber-50',
    },
    {
      label: 'KYC Verifications Pending',
      value: metrics?.pending_kyc || 0,
      icon: FileCheck2,
      color: 'text-indigo-600',
      bg: 'bg-indigo-50',
    },
    {
      label: 'Active Loans Servicing',
      value: metrics?.active_loans || 0,
      icon: TrendingUp,
      color: 'text-teal-600',
      bg: 'bg-teal-50',
    },
    {
      label: 'Simulated Total Disbursed',
      value: formatCurrency(metrics?.total_disbursed_paise),
      icon: DollarSign,
      color: 'text-emerald-600',
      bg: 'bg-emerald-50',
    },
    {
      label: 'Simulated Total Repaid',
      value: formatCurrency(metrics?.total_repaid_paise),
      icon: CheckCircle2,
      color: 'text-cyan-600',
      bg: 'bg-cyan-50',
    },
    {
      label: 'Outstanding Principal Pool',
      value: formatCurrency(metrics?.total_outstanding_principal_paise),
      icon: CreditCard,
      color: 'text-purple-600',
      bg: 'bg-purple-50',
    },
    {
      label: 'Overdue Accounts',
      value: metrics?.overdue_loans || 0,
      icon: AlertCircle,
      color: 'text-rose-600',
      bg: 'bg-rose-50',
    },
  ];

  return (
    <div className="flex-1 overflow-y-auto">
      <Header
        title="Executive Overview"
        subtitle="Real-time aggregation of synthetic lending metrics & financial pools"
      />

      <main className="p-8 max-w-7xl mx-auto space-y-8">
        {/* KPI Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          {statCards.map((card, idx) => {
            const Icon = card.icon;
            return (
              <div
                key={idx}
                className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-sm hover:shadow-md transition-shadow"
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    {card.label}
                  </span>
                  <div className={`p-2 rounded-xl ${card.bg}`}>
                    <Icon className={`w-5 h-5 ${card.color}`} />
                  </div>
                </div>
                <div className="text-2xl font-bold text-slate-900 tracking-tight">
                  {card.value}
                </div>
              </div>
            );
          })}
        </div>

        {/* Operational Highlights */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
            <h3 className="text-base font-bold text-slate-900 mb-4 flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-teal-500 inline-block"></span>
              <span>Lending Pipeline Summary</span>
            </h3>
            <div className="space-y-3.5">
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-sm font-medium text-slate-600">Total Loan Applications</span>
                <span className="text-sm font-bold text-slate-900">{metrics?.total_applications || 0}</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-sm font-medium text-slate-600">Approved Applications</span>
                <span className="text-sm font-bold text-emerald-600">{metrics?.approved_applications || 0}</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-sm font-medium text-slate-600">Rejected Applications</span>
                <span className="text-sm font-bold text-rose-600">{metrics?.rejected_applications || 0}</span>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-slate-900 to-slate-800 text-white rounded-2xl p-6 shadow-sm flex flex-col justify-between">
            <div>
              <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-teal-500/20 text-teal-300 border border-teal-500/30 uppercase tracking-wider">
                Financial Guardrails
              </span>
              <h3 className="text-xl font-bold mt-4 tracking-tight">
                Zero Floating-Point Financial Engine
              </h3>
              <p className="text-sm text-slate-300 mt-2 leading-relaxed">
                Every calculation across reducing-balance EMI, GST fees, IRR-based APR, and balanced general ledger journals is persisted strictly in integer paise. No simulated client-side-only mutations.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-slate-700/60 flex items-center justify-between text-xs text-slate-400">
              <span>Database: PostgreSQL 16 (Paise)</span>
              <span>Ledger: Double-Entry Balanced</span>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};
