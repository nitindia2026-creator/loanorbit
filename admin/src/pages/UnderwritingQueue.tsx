import React, { useEffect, useState } from 'react';
import { CheckCircle, XCircle, ArrowUpRight, DollarSign } from 'lucide-react';
import { Header } from '../components/Header';
import { api } from '../lib/api';

export const UnderwritingQueue: React.FC = () => {
  const [queue, setQueue] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedApp, setSelectedApp] = useState<any | null>(null);
  const [remarks, setRemarks] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  const fetchQueue = () => {
    setLoading(true);
    api
      .getUnderwritingQueue()
      .then((data) => setQueue(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchQueue();
  }, []);

  const handleDecision = async (decision: 'APPROVED' | 'REJECTED') => {
    if (!selectedApp) return;
    setActionLoading(true);
    try {
      await api.decideUnderwriting(selectedApp.id, {
        decision,
        remarks: remarks || `Underwriter ${decision.toLowerCase()} credit review decision.`,
      });
      setSelectedApp(null);
      setRemarks('');
      fetchQueue();
    } catch (err: any) {
      alert(err.message || 'Underwriting action failed.');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto">
      <Header
        title="Credit Underwriting Desk"
        subtitle="Evaluate loan applications, risk bands, credit metrics & issue sanctioned offers"
      />

      <main className="p-8 max-w-7xl mx-auto space-y-6">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-6 border-b border-slate-100 flex items-center justify-between">
            <h3 className="font-bold text-slate-900">Applications Awaiting Credit Decision ({queue.length})</h3>
            <span className="text-xs text-slate-500 font-medium">
              Policy Engine: v1.0 Standard
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50/75 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wider">
                  <th className="py-4 px-6">App Reference</th>
                  <th className="py-4 px-6">Requested Principal</th>
                  <th className="py-4 px-6">Tenure</th>
                  <th className="py-4 px-6">Loan Purpose</th>
                  <th className="py-4 px-6">Submission Date</th>
                  <th className="py-4 px-6 text-right">Credit Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="py-12 text-center text-slate-400">
                      Loading underwriting desk queue...
                    </td>
                  </tr>
                ) : queue.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-12 text-center text-slate-400">
                      No applications currently awaiting underwriting review.
                    </td>
                  </tr>
                ) : (
                  queue.map((app) => (
                    <tr key={app.id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="py-4 px-6 font-mono font-bold text-teal-700">
                        {app.application_reference}
                      </td>
                      <td className="py-4 px-6 font-bold text-slate-900">
                        ₹{(app.requested_amount_paise / 100).toLocaleString('en-IN')}
                      </td>
                      <td className="py-4 px-6 text-slate-700">
                        {app.requested_tenure_months} Months
                      </td>
                      <td className="py-4 px-6 text-xs text-slate-600 max-w-xs truncate">
                        {app.purpose}
                      </td>
                      <td className="py-4 px-6 text-xs text-slate-500">
                        {new Date(app.created_at).toLocaleDateString('en-IN')}
                      </td>
                      <td className="py-4 px-6 text-right">
                        <button
                          onClick={() => setSelectedApp(app)}
                          className="px-3.5 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold transition-all shadow-sm flex items-center space-x-1 ml-auto"
                        >
                          <span>Underwrite</span>
                          <ArrowUpRight className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Underwriting Decision Modal */}
        {selectedApp && (
          <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-100 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h4 className="font-bold text-slate-900 text-lg">
                  Credit Review: {selectedApp.application_reference}
                </h4>
                <button
                  onClick={() => setSelectedApp(null)}
                  className="text-slate-400 hover:text-slate-600 font-bold"
                >
                  ✕
                </button>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-2">
                <div className="flex justify-between">
                  <span className="text-slate-500">Requested Principal:</span>
                  <span className="font-bold text-slate-900">
                    ₹{(selectedApp.requested_amount_paise / 100).toLocaleString('en-IN')}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Requested Tenure:</span>
                  <span className="font-bold text-slate-900">{selectedApp.requested_tenure_months} Months</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Declared Purpose:</span>
                  <span className="text-slate-800 italic">{selectedApp.purpose}</span>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Underwriter Decision Justification
                </label>
                <textarea
                  value={remarks}
                  onChange={(e) => setRemarks(e.target.value)}
                  placeholder="Record risk band evaluation, FOIR ratio compliance, and credit assessment remarks..."
                  rows={3}
                  className="w-full p-3 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div className="flex space-x-3 pt-2">
                <button
                  onClick={() => handleDecision('REJECTED')}
                  disabled={actionLoading}
                  className="flex-1 py-2.5 rounded-xl border border-rose-300 text-rose-700 font-semibold text-sm hover:bg-rose-50 flex items-center justify-center space-x-2 transition-all"
                >
                  <XCircle className="w-4 h-4" />
                  <span>Reject Loan</span>
                </button>
                <button
                  onClick={() => handleDecision('APPROVED')}
                  disabled={actionLoading}
                  className="flex-1 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-semibold text-sm flex items-center justify-center space-x-2 transition-all shadow-md shadow-teal-600/20"
                >
                  <CheckCircle className="w-4 h-4" />
                  <span>Approve & Issue Offer</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};
