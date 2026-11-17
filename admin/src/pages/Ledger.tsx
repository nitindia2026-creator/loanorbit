import React, { useEffect, useState } from 'react';
import { BookOpen, Scale, ArrowDownRight, ArrowUpRight, CheckCircle2 } from 'lucide-react';
import { Header } from '../components/Header';
import { api } from '../lib/api';

export const Ledger: React.FC = () => {
  const [accounts, setAccounts] = useState<any[]>([]);
  const [entries, setEntries] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'ACCOUNTS' | 'JOURNALS'>('ACCOUNTS');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.getLedgerAccounts(), api.getJournalEntries()])
      .then(([accs, jnls]) => {
        setAccounts(accs);
        setEntries(jnls);
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex-1 overflow-y-auto">
      <Header
        title="Double-Entry General Ledger"
        subtitle="Mathematical source-of-truth accounting records, chart of accounts & balanced journal entries"
      />

      <main className="p-8 max-w-7xl mx-auto space-y-6">
        {/* Navigation Tabs */}
        <div className="flex space-x-2 border-b border-slate-200 pb-3">
          <button
            onClick={() => setActiveTab('ACCOUNTS')}
            className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
              activeTab === 'ACCOUNTS'
                ? 'bg-teal-600 text-white shadow-sm'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            Chart of Accounts ({accounts.length})
          </button>
          <button
            onClick={() => setActiveTab('JOURNALS')}
            className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
              activeTab === 'JOURNALS'
                ? 'bg-teal-600 text-white shadow-sm'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            Posted Journal Entries ({entries.length})
          </button>
        </div>

        {activeTab === 'ACCOUNTS' ? (
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50/75 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wider">
                  <th className="py-4 px-6">Account Code</th>
                  <th className="py-4 px-6">Account Name</th>
                  <th className="py-4 px-6">Classification</th>
                  <th className="py-4 px-6 text-right">Running Balance</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {accounts.map((acc) => (
                  <tr key={acc.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-4 px-6 font-mono font-bold text-teal-700">{acc.account_code}</td>
                    <td className="py-4 px-6 font-semibold text-slate-900">{acc.account_name}</td>
                    <td className="py-4 px-6">
                      <span className="inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700">
                        {acc.account_type}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-right font-mono font-bold text-slate-900">
                      ₹{(acc.balance_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="space-y-4">
            {entries.length === 0 ? (
              <div className="bg-white rounded-2xl p-12 text-center text-slate-400 border border-slate-200">
                No posted journal entries recorded yet.
              </div>
            ) : (
              entries.map((j) => (
                <div key={j.id} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-3">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                    <div>
                      <span className="font-mono font-bold text-teal-700 text-sm mr-3">
                        {j.entry_reference}
                      </span>
                      <span className="text-xs px-2.5 py-1 rounded-md font-bold bg-teal-50 text-teal-700">
                        {j.entry_type}
                      </span>
                    </div>
                    <span className="text-xs text-slate-500">
                      {new Date(j.posted_at).toLocaleString('en-IN')}
                    </span>
                  </div>

                  <p className="text-xs text-slate-600 italic">{j.description}</p>

                  <div className="bg-slate-50 rounded-xl p-3 divide-y divide-slate-200/60 text-xs">
                    {j.lines?.map((line: any) => (
                      <div key={line.id} className="py-1.5 flex items-center justify-between font-mono">
                        <div className="flex items-center space-x-2">
                          <span
                            className={`font-bold px-1.5 py-0.5 rounded ${
                              line.entry_direction === 'DEBIT'
                                ? 'bg-blue-100 text-blue-700'
                                : 'bg-emerald-100 text-emerald-700'
                            }`}
                          >
                            {line.entry_direction}
                          </span>
                          <span className="text-slate-700 font-sans">{line.account_id}</span>
                        </div>
                        <span className="font-bold text-slate-900">
                          ₹{(line.amount_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </main>
    </div>
  );
};
