import React, { useEffect, useState } from 'react';
import { History, Shield, Lock } from 'lucide-react';
import { Header } from '../components/Header';
import { api } from '../lib/api';

export const AuditLogs: React.FC = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getAuditLogs()
      .then((data) => setLogs(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex-1 overflow-y-auto">
      <Header
        title="Security & Audit Logs"
        subtitle="Append-only regulatory audit trail capturing all administrative, underwriting & financial actions"
      />

      <main className="p-8 max-w-7xl mx-auto space-y-6">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-6 border-b border-slate-100 flex items-center justify-between">
            <h3 className="font-bold text-slate-900">Security Audit Trail</h3>
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-100 text-slate-700">
              Immutable Records
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50/75 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wider">
                  <th className="py-4 px-6">Timestamp (UTC)</th>
                  <th className="py-4 px-6">Actor Type</th>
                  <th className="py-4 px-6">Action / Event</th>
                  <th className="py-4 px-6">Target Entity</th>
                  <th className="py-4 px-6">Target Reference</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {loading ? (
                  <tr>
                    <td colSpan={5} className="py-12 text-center text-slate-400">
                      Loading audit event logs...
                    </td>
                  </tr>
                ) : logs.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-12 text-center text-slate-400">
                      No security audit events recorded in current session.
                    </td>
                  </tr>
                ) : (
                  logs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="py-4 px-6 text-xs text-slate-500 font-mono">
                        {new Date(log.created_at).toISOString()}
                      </td>
                      <td className="py-4 px-6">
                        <span className="inline-block px-2 py-0.5 rounded text-xs font-bold bg-slate-100 text-slate-700">
                          {log.actor_type}
                        </span>
                      </td>
                      <td className="py-4 px-6 font-semibold text-slate-900">{log.action}</td>
                      <td className="py-4 px-6 text-xs text-slate-600">{log.target_entity}</td>
                      <td className="py-4 px-6 font-mono text-xs text-teal-700 font-bold">
                        {log.target_id.slice(0, 8)}...
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
};
