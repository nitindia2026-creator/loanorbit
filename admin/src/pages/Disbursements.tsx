import React, { useEffect, useState } from 'react';
import { Send, CheckCircle2, AlertCircle, RefreshCw, Landmark } from 'lucide-react';
import { api } from '../lib/api';

interface DisbursementItem {
  id: string;
  loan_id: string;
  amount_paise: number;
  bank_verification_id: string;
  mock_provider_reference: string | null;
  status: string;
  failure_reason: string | null;
  disbursed_at: string | null;
  created_at: string;
}

export const Disbursements: React.FC = () => {
  const [disbursements, setDisbursements] = useState<DisbursementItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoanId, setActionLoanId] = useState('');
  const [triggering, setTriggering] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const fetchDisbursements = async () => {
    try {
      setLoading(true);
      const res = await api.get('/disbursements');
      setDisbursements(res.data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDisbursements();
  }, []);

  const handleTriggerDisbursement = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!actionLoanId.trim()) return;

    try {
      setTriggering(true);
      setMessage(null);
      const res = await api.post(`/disbursements/trigger/${actionLoanId.trim()}`, {
        idempotency_key: `DISB-${actionLoanId.slice(0, 8)}-${Date.now()}`,
      });
      setMessage({
        text: `Disbursement triggered successfully! Loan status: ${res.data.loan_status}`,
        type: 'success',
      });
      setActionLoanId('');
      fetchDisbursements();
    } catch (err: any) {
      setMessage({
        text: err.response?.data?.detail?.message || 'Failed to trigger disbursement.',
        type: 'error',
      });
    } finally {
      setTriggering(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center space-x-2">
            <Landmark className="w-7 h-7 text-teal-400" />
            <span>Disbursement Desk</span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Simulated lender escrow disbursement and fund release operations.
          </p>
        </div>
        <button
          onClick={fetchDisbursements}
          className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-lg bg-slate-800 text-slate-300 hover:text-white border border-slate-700 hover:border-slate-600 text-sm font-medium transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Desk</span>
        </button>
      </div>

      {/* Manual Trigger Card */}
      <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 shadow-sm">
        <h2 className="text-sm font-semibold text-white uppercase tracking-wider mb-3">
          Execute Disbursement
        </h2>
        <form onSubmit={handleTriggerDisbursement} className="flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            placeholder="Enter Loan ID (e.g. UUID)"
            value={actionLoanId}
            onChange={(e) => setActionLoanId(e.target.value)}
            className="flex-1 px-4 py-2.5 rounded-lg bg-slate-800/80 border border-slate-700 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-teal-500"
          />
          <button
            type="submit"
            disabled={triggering || !actionLoanId.trim()}
            className="inline-flex items-center justify-center space-x-2 px-5 py-2.5 rounded-lg bg-teal-600 hover:bg-teal-500 text-white font-medium text-sm transition-colors disabled:opacity-50"
          >
            <Send className="w-4 h-4" />
            <span>{triggering ? 'Disbursing...' : 'Trigger Fund Transfer'}</span>
          </button>
        </form>

        {message && (
          <div
            className={`mt-3 p-3 rounded-lg text-sm flex items-center space-x-2 ${
              message.type === 'success'
                ? 'bg-teal-500/10 text-teal-400 border border-teal-500/20'
                : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
            }`}
          >
            {message.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 shrink-0" />
            )}
            <span>{message.text}</span>
          </div>
        )}
      </div>

      {/* Disbursement Records Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900 overflow-hidden shadow-sm">
        <div className="px-6 py-4 border-b border-slate-800 flex justify-between items-center">
          <h2 className="text-base font-semibold text-white">Disbursement Events</h2>
          <span className="text-xs font-medium text-slate-400">Total: {disbursements.length}</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/40 text-slate-400 font-medium">
                <th className="py-3 px-4">Event ID</th>
                <th className="py-3 px-4">Loan ID</th>
                <th className="py-3 px-4">Amount</th>
                <th className="py-3 px-4">Provider Ref</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Disbursed At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500">
                    Loading disbursement records...
                  </td>
                </tr>
              ) : disbursements.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500">
                    No disbursement transactions recorded yet.
                  </td>
                </tr>
              ) : (
                disbursements.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4 font-mono text-xs text-slate-400">
                      {item.id.slice(0, 8)}...
                    </td>
                    <td className="py-3 px-4 font-mono text-xs text-teal-400">
                      {item.loan_id.slice(0, 8)}...
                    </td>
                    <td className="py-3 px-4 font-semibold text-white">
                      ₹{(item.amount_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-4 font-mono text-xs text-slate-400">
                      {item.mock_provider_reference || '—'}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${
                          item.status === 'SUCCESS'
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                            : item.status === 'FAILED'
                            ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                            : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                        }`}
                      >
                        {item.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-xs text-slate-400">
                      {item.disbursed_at ? new Date(item.disbursed_at).toLocaleString() : 'Pending'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
