import React, { useEffect, useState } from 'react';
import { FileCheck, FileX, ShieldAlert, CheckCircle2, AlertCircle } from 'lucide-react';
import { Header } from '../components/Header';
import { api } from '../lib/api';

export const KYCQueue: React.FC = () => {
  const [queue, setQueue] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCase, setSelectedCase] = useState<any | null>(null);
  const [remarks, setRemarks] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  const fetchQueue = () => {
    setLoading(true);
    api
      .getKYCQueue()
      .then((data) => setQueue(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchQueue();
  }, []);

  const handleDecision = async (decision: 'VERIFIED' | 'REJECTED') => {
    if (!selectedCase) return;
    setActionLoading(true);
    try {
      await api.decideKYC(selectedCase.id, {
        decision,
        remarks: remarks || `Officer ${decision.toLowerCase()} decision in sandbox desk.`,
        reason_code: decision === 'REJECTED' ? 'SYNTHETIC_DATA_INVALID' : undefined,
      });
      setSelectedCase(null);
      setRemarks('');
      fetchQueue();
    } catch (err: any) {
      alert(err.message || 'Decision failed.');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto">
      <Header
        title="KYC Verification Desk"
        subtitle="Review uploaded synthetic documents & make regulatory verification decisions"
      />

      <main className="p-8 max-w-7xl mx-auto space-y-6">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-6 border-b border-slate-100 flex items-center justify-between">
            <h3 className="font-bold text-slate-900">Pending Identity Cases ({queue.length})</h3>
            <span className="text-xs text-slate-500 font-medium">
              Deterministic Simulation Mode Active
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50/75 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wider">
                  <th className="py-4 px-6">Case ID</th>
                  <th className="py-4 px-6">ID Type & Number</th>
                  <th className="py-4 px-6">Submitted At</th>
                  <th className="py-4 px-6">Documents Attached</th>
                  <th className="py-4 px-6 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {loading ? (
                  <tr>
                    <td colSpan={5} className="py-12 text-center text-slate-400">
                      Loading pending verification queue...
                    </td>
                  </tr>
                ) : queue.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-12 text-center text-slate-400">
                      No pending KYC verification cases. Queue is clean!
                    </td>
                  </tr>
                ) : (
                  queue.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="py-4 px-6 font-mono text-xs font-bold text-slate-800">
                        {item.id.slice(0, 8)}...
                      </td>
                      <td className="py-4 px-6 font-medium text-slate-900">
                        <span className="font-bold text-teal-700 mr-2">{item.id_type}:</span>
                        <span>{item.id_number_masked}</span>
                      </td>
                      <td className="py-4 px-6 text-xs text-slate-500">
                        {new Date(item.created_at).toLocaleString('en-IN')}
                      </td>
                      <td className="py-4 px-6">
                        <span className="inline-block px-2.5 py-1 rounded-md text-xs font-semibold bg-slate-100 text-slate-700">
                          {item.documents?.length || 1} Document(s)
                        </span>
                      </td>
                      <td className="py-4 px-6 text-right">
                        <button
                          onClick={() => setSelectedCase(item)}
                          className="px-3.5 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold transition-all shadow-sm"
                        >
                          Review & Decide
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Decision Modal */}
        {selectedCase && (
          <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-100 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h4 className="font-bold text-slate-900 text-lg">
                  Decide KYC Case: {selectedCase.id.slice(0, 8)}
                </h4>
                <button
                  onClick={() => setSelectedCase(null)}
                  className="text-slate-400 hover:text-slate-600 font-bold"
                >
                  ✕
                </button>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-2">
                <div className="flex justify-between">
                  <span className="text-slate-500">Document Type:</span>
                  <span className="font-bold text-slate-800">{selectedCase.id_type}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Masked ID Number:</span>
                  <span className="font-mono font-bold text-slate-800">{selectedCase.id_number_masked}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Synthetic Status:</span>
                  <span className="text-amber-600 font-bold">Simulated Sandbox Record</span>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Officer Remarks / Audit Reason
                </label>
                <textarea
                  value={remarks}
                  onChange={(e) => setRemarks(e.target.value)}
                  placeholder="Enter verification notes or rejection justification..."
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
                  <FileX className="w-4 h-4" />
                  <span>Reject KYC</span>
                </button>
                <button
                  onClick={() => handleDecision('VERIFIED')}
                  disabled={actionLoading}
                  className="flex-1 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-semibold text-sm flex items-center justify-center space-x-2 transition-all shadow-md shadow-teal-600/20"
                >
                  <FileCheck className="w-4 h-4" />
                  <span>Approve & Verify</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};
