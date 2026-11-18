import React, { useEffect, useState } from 'react';
import { Headphones, Send, RefreshCw, MessageSquare } from 'lucide-react';
import { api } from '../lib/api';

interface SupportMessage {
  id: string;
  sender_type: string;
  sender_id: string;
  message: string;
  is_internal_note: boolean;
  created_at: string;
}

interface SupportTicket {
  id: string;
  ticket_reference: string;
  user_id: string;
  category: string;
  subject: string;
  description: string;
  status: string;
  assigned_admin_id: string | null;
  created_at: string;
  messages: SupportMessage[];
}

export const Support: React.FC = () => {
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTicket, setSelectedTicket] = useState<SupportTicket | null>(null);
  const [replyText, setReplyText] = useState('');
  const [sending, setSending] = useState(false);

  const fetchTickets = async () => {
    try {
      setLoading(true);
      const res = await api.get('/support/admin/tickets');
      setTickets(res.data);
      if (selectedTicket) {
        const updated = res.data.find((t: SupportTicket) => t.id === selectedTicket.id);
        if (updated) setSelectedTicket(updated);
      }
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTickets();
  }, []);

  const handleSendReply = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTicket || !replyText.trim()) return;

    try {
      setSending(true);
      await api.post(`/support/admin/tickets/${selectedTicket.id}/reply`, {
        message: replyText.trim(),
        is_internal_note: false,
      });
      setReplyText('');
      fetchTickets();
    } catch (err: any) {
      alert('Failed to send reply.');
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center space-x-2">
            <Headphones className="w-7 h-7 text-teal-400" />
            <span>Customer Support Desk</span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Resolve borrower inquiries, payment issues, and account assistance tickets.
          </p>
        </div>
        <button
          onClick={fetchTickets}
          className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-lg bg-slate-800 text-slate-300 hover:text-white border border-slate-700 hover:border-slate-600 text-sm font-medium transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Tickets</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Ticket List */}
        <div className="lg:col-span-1 rounded-xl border border-slate-800 bg-slate-900 overflow-hidden shadow-sm flex flex-col h-[650px]">
          <div className="px-5 py-4 border-b border-slate-800 flex justify-between items-center">
            <h2 className="text-sm font-semibold text-white uppercase tracking-wider">
              Tickets ({tickets.length})
            </h2>
          </div>
          <div className="flex-1 overflow-y-auto divide-y divide-slate-800/60">
            {loading ? (
              <div className="p-6 text-center text-slate-500 text-sm">Loading tickets...</div>
            ) : tickets.length === 0 ? (
              <div className="p-6 text-center text-slate-500 text-sm">No support tickets found.</div>
            ) : (
              tickets.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setSelectedTicket(t)}
                  className={`w-full text-left p-4 transition-colors flex flex-col gap-1.5 ${
                    selectedTicket?.id === t.id ? 'bg-slate-800/80' : 'hover:bg-slate-800/30'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs text-teal-400 font-medium">
                      {t.ticket_reference}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        t.status === 'RESOLVED'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : t.status === 'IN_PROGRESS'
                          ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                          : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                      }`}
                    >
                      {t.status}
                    </span>
                  </div>
                  <p className="text-sm font-medium text-slate-200 line-clamp-1">{t.subject}</p>
                  <p className="text-xs text-slate-400 line-clamp-1">{t.description}</p>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Ticket Chat View */}
        <div className="lg:col-span-2 rounded-xl border border-slate-800 bg-slate-900 overflow-hidden shadow-sm flex flex-col h-[650px]">
          {selectedTicket ? (
            <>
              {/* Ticket Details Header */}
              <div className="p-5 border-b border-slate-800 bg-slate-950/40">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-base font-semibold text-white">{selectedTicket.subject}</h3>
                    <p className="text-xs text-slate-400 mt-1">
                      Reference: <span className="font-mono text-teal-400">{selectedTicket.ticket_reference}</span> | Category: {selectedTicket.category}
                    </p>
                  </div>
                  <span className="text-xs text-slate-500">
                    {new Date(selectedTicket.created_at).toLocaleString()}
                  </span>
                </div>
              </div>

              {/* Messages Body */}
              <div className="flex-1 p-5 overflow-y-auto space-y-4">
                {selectedTicket.messages.map((m) => (
                  <div
                    key={m.id}
                    className={`flex flex-col ${
                      m.sender_type === 'ADMIN' ? 'items-end' : 'items-start'
                    }`}
                  >
                    <div
                      className={`max-w-[80%] rounded-xl px-4 py-3 text-sm ${
                        m.sender_type === 'ADMIN'
                          ? 'bg-teal-600 text-white rounded-br-none'
                          : 'bg-slate-800 text-slate-200 rounded-bl-none border border-slate-700'
                      }`}
                    >
                      <p className="text-[10px] font-semibold opacity-75 mb-1 uppercase tracking-wider">
                        {m.sender_type}
                      </p>
                      <p className="whitespace-pre-wrap">{m.message}</p>
                    </div>
                    <span className="text-[10px] text-slate-500 mt-1">
                      {new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                ))}
              </div>

              {/* Reply Box */}
              <form onSubmit={handleSendReply} className="p-4 border-t border-slate-800 bg-slate-950/60 flex gap-2">
                <input
                  type="text"
                  placeholder="Type an official response..."
                  value={replyText}
                  onChange={(e) => setReplyText(e.target.value)}
                  className="flex-1 px-4 py-2.5 rounded-lg bg-slate-800 border border-slate-700 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-teal-500"
                />
                <button
                  type="submit"
                  disabled={sending || !replyText.trim()}
                  className="inline-flex items-center space-x-1.5 px-4 py-2.5 rounded-lg bg-teal-600 hover:bg-teal-500 text-white font-medium text-sm transition-colors disabled:opacity-50"
                >
                  <Send className="w-4 h-4" />
                  <span>{sending ? 'Sending...' : 'Reply'}</span>
                </button>
              </form>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-slate-500">
              <MessageSquare className="w-12 h-12 stroke-1 mb-3 text-slate-600" />
              <p className="text-sm">Select a ticket from the left panel to review messages and reply.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
