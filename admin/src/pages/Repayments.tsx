import React, { useEffect, useState } from 'react';
import { RotateCcw, CheckCircle2, AlertCircle, RefreshCw, CreditCard } from 'lucide-react';
import { api } from '../lib/api';

interface AllocationItem {
  id: string;
  instalment_id: string;
  allocated_principal_paise: number;
  allocated_interest_paise: number;
  allocated_charges_paise: number;
}

interface PaymentItem {
  id: string;
  loan_id: string;
  amount_paise: number;
  payment_method: string;
  status: string;
  provider_reference: string | null;
  paid_at: string;
  allocations: AllocationItem[];
}

export const Repayments: React.FC = () => {
  const [payments, setPayments] = useState<PaymentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [reversingId, setReversingId] = useState<string | null>(null);
  const [reason, setReason] = useState('Customer dispute chargeback');
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const fetchPayments = async () => {
    try {
      setLoading(true);
      const res = await api.get('/repayments/all');
      setPayments(res.data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPayments();
  }, []);

  const handleReversePayment = async (paymentId: string) => {
    if (!confirm('Are you sure you want to reverse this payment and create compensating ledger entries?')) {
      return;
    }

    try {
      setReversingId(paymentId);
      setMessage(null);
      await api.post(`/repayments/${paymentId}/reverse`, { reason });
      setMessage({
        text: `Payment ${paymentId.slice(0, 8)} successfully reversed and compensated.`,
        type: 'success',
      });
      fetchPayments();
    } catch (err: any) {
      setMessage({
        text: err.response?.data?.detail?.message || 'Failed to reverse payment.',
        type: 'error',
      });
    } finally {
      setReversingId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center space-x-2">
            <CreditCard className="w-7 h-7 text-teal-400" />
            <span>Repayments & Settlements</span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Collections tracking, payment allocations waterfall, and compensating reversal desk.
          </p>
        </div>
        <button
          onClick={fetchPayments}
          className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-lg bg-slate-800 text-slate-300 hover:text-white border border-slate-700 hover:border-slate-600 text-sm font-medium transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Desk</span>
        </button>
      </div>

      {message && (
        <div
          className={`p-3.5 rounded-lg text-sm flex items-center space-x-2 ${
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

      {/* Repayments Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900 overflow-hidden shadow-sm">
        <div className="px-6 py-4 border-b border-slate-800 flex justify-between items-center">
          <h2 className="text-base font-semibold text-white">Collections Ledger</h2>
          <span className="text-xs font-medium text-slate-400">Total: {payments.length}</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/40 text-slate-400 font-medium">
                <th className="py-3 px-4">Payment ID</th>
                <th className="py-3 px-4">Loan ID</th>
                <th className="py-3 px-4">Amount</th>
                <th className="py-3 px-4">Method</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Paid At</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    Loading repayment records...
                  </td>
                </tr>
              ) : payments.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    No repayment records found.
                  </td>
                </tr>
              ) : (
                payments.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4 font-mono text-xs text-slate-400">
                      {p.id.slice(0, 8)}...
                    </td>
                    <td className="py-3 px-4 font-mono text-xs text-teal-400">
                      {p.loan_id.slice(0, 8)}...
                    </td>
                    <td className="py-3 px-4 font-semibold text-white">
                      ₹{(p.amount_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-4 font-mono text-xs text-slate-400">
                      {p.payment_method}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${
                          p.status === 'SUCCESS'
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                            : p.status === 'REVERSED'
                            ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                            : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                        }`}
                      >
                        {p.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-xs text-slate-400">
                      {new Date(p.paid_at).toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right">
                      {p.status === 'SUCCESS' ? (
                        <button
                          onClick={() => handleReversePayment(p.id)}
                          disabled={reversingId === p.id}
                          className="inline-flex items-center space-x-1.5 px-2.5 py-1.5 rounded-md bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 border border-rose-500/20 text-xs font-medium transition-colors disabled:opacity-50"
                        >
                          <RotateCcw className="w-3.5 h-3.5" />
                          <span>{reversingId === p.id ? 'Reversing...' : 'Reverse'}</span>
                        </button>
                      ) : (
                        <span className="text-xs text-slate-500">Reversed</span>
                      )}
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
