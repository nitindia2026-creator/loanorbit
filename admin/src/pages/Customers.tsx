import React, { useEffect, useState } from 'react';
import { Search, ShieldCheck, Mail, Phone, Calendar } from 'lucide-react';
import { Header } from '../components/Header';
import { api } from '../lib/api';

export const Customers: React.FC = () => {
  const [customers, setCustomers] = useState<any[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getCustomers()
      .then((data) => setCustomers(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const filtered = customers.filter(
    (c) =>
      c.mobile_number?.toLowerCase().includes(search.toLowerCase()) ||
      c.profile?.full_name?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="flex-1 overflow-y-auto">
      <Header
        title="Customer Directory"
        subtitle="Manage verified borrower personas, onboarding states & credit profiles"
      />

      <main className="p-8 max-w-7xl mx-auto space-y-6">
        {/* Search Bar */}
        <div className="flex items-center justify-between">
          <div className="relative w-80">
            <Search className="w-4 h-4 absolute left-3.5 top-3 text-slate-400" />
            <input
              type="text"
              placeholder="Search by name or mobile..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 bg-white"
            />
          </div>
          <span className="text-xs text-slate-500 font-semibold">
            Showing {filtered.length} synthetic customer accounts
          </span>
        </div>

        {/* Data Table */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50/75 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wider">
                  <th className="py-4 px-6">Customer</th>
                  <th className="py-4 px-6">Contact Details</th>
                  <th className="py-4 px-6">Employment & Income</th>
                  <th className="py-4 px-6">Location</th>
                  <th className="py-4 px-6">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {loading ? (
                  <tr>
                    <td colSpan={5} className="py-12 text-center text-slate-400">
                      Loading customer records...
                    </td>
                  </tr>
                ) : filtered.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-12 text-center text-slate-400">
                      No matching customer accounts found.
                    </td>
                  </tr>
                ) : (
                  filtered.map((c) => (
                    <tr key={c.id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="py-4 px-6">
                        <div className="font-bold text-slate-900">
                          {c.profile?.full_name || 'Incomplete Profile'}
                        </div>
                        <div className="text-xs text-slate-400 font-mono mt-0.5">
                          ID: {c.id.slice(0, 8)}...
                        </div>
                      </td>
                      <td className="py-4 px-6 space-y-1">
                        <div className="flex items-center space-x-1.5 text-xs text-slate-600 font-medium">
                          <Phone className="w-3.5 h-3.5 text-slate-400" />
                          <span>{c.mobile_number}</span>
                        </div>
                        <div className="flex items-center space-x-1.5 text-xs text-slate-600">
                          <Mail className="w-3.5 h-3.5 text-slate-400" />
                          <span>{c.email || 'N/A'}</span>
                        </div>
                      </td>
                      <td className="py-4 px-6">
                        <div className="font-semibold text-slate-800">
                          {c.profile?.employment_type || 'N/A'}
                        </div>
                        <div className="text-xs text-teal-600 font-bold mt-0.5">
                          {c.profile?.monthly_income_paise
                            ? `₹${(c.profile.monthly_income_paise / 100).toLocaleString('en-IN')}/mo`
                            : 'N/A'}
                        </div>
                      </td>
                      <td className="py-4 px-6 text-xs text-slate-600">
                        {c.profile?.city ? `${c.profile.city}, ${c.profile.state}` : 'N/A'}
                      </td>
                      <td className="py-4 px-6">
                        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          <ShieldCheck className="w-3 h-3 mr-1" />
                          Verified Persona
                        </span>
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
