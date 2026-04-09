"use client";

import { useState, useEffect } from "react";
import { format } from "date-fns";
import api from "@/lib/api";
import { Mail, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";

interface NotificationLog {
  id: string;
  template_key: string;
  recipient_email: string;
  subject: string;
  created_at: string;
  status: string;
  error: string;
}

export default function NotificationLogsSection({ expedienteId, isCeo }: { expedienteId: string, isCeo: boolean }) {
  const [logs, setLogs] = useState<NotificationLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchLogs = async (quiet = false) => {
    if (!quiet) setLoading(true);
    else setRefreshing(true);
    try {
      const res = await api.get(`/api/notifications/log/?expediente=${expedienteId}`);
      setLogs(res.data.results || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [expedienteId]);

  if (!isCeo) return null; // CEO only section per requirements

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'sent': return <span className="px-2 py-0.5 text-[9px] uppercase rounded-full bg-[rgba(117,203,179,0.15)] text-mint font-bold">Sent</span>;
      case 'skipped': return <span className="px-2 py-0.5 text-[9px] uppercase rounded-full bg-[rgba(255,255,255,0.1)] text-[rgba(255,255,255,0.6)] font-bold">Skipped</span>;
      case 'disabled': return <span className="px-2 py-0.5 text-[9px] uppercase rounded-full bg-yellow-500/20 text-yellow-400 font-bold">Disabled</span>;
      case 'exhausted': return <span className="px-2 py-0.5 text-[9px] uppercase rounded-full bg-red-500/20 text-red-400 font-bold">Exhausted</span>;
      default: return <span className="px-2 py-0.5 text-[9px] uppercase rounded-full bg-[rgba(255,255,255,0.1)] text-white font-bold">{status}</span>;
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="heading-sm font-semibold flex items-center gap-2 text-[var(--interactive)]">
          <Mail size={16} /> Emails Enviados
        </h2>
        <button
          className="btn btn-sm btn-ghost p-1 h-auto"
          onClick={() => fetchLogs(true)}
          disabled={refreshing}
        >
          <RefreshCw size={14} className={cn(refreshing && "animate-spin text-[var(--interactive)]")} />
        </button>
      </div>
      
      {loading && logs.length === 0 ? (
        <div className="text-xs text-[var(--text-tertiary)] py-4 text-center">Cargando emails...</div>
      ) : logs.length === 0 ? (
        <div className="text-xs text-[var(--text-tertiary)] py-4 text-center bg-[var(--surface-hover)] rounded border border-dashed border-[var(--border)]">
          No se han enviado emails para este expediente.
        </div>
      ) : (
        <div className="space-y-2 max-h-64 overflow-y-auto pr-1 custom-scrollbar">
          {logs.map((log) => (
             <div key={log.id} className="p-3 bg-[var(--bg-alt)] border border-[var(--border)] rounded flex flex-col gap-1.5 hover:border-[var(--interactive)] transition-colors">
               <div className="flex items-start justify-between">
                 <div className="flex flex-col">
                   <div className="flex items-center gap-2">
                     <span className="text-xs font-semibold text-[var(--interactive)]">{log.template_key}</span>
                     {getStatusBadge(log.status)}
                   </div>
                   <span className="text-[10px] text-[var(--text-tertiary)] mt-0.5">{log.recipient_email}</span>
                 </div>
                 <span className="text-[10px] text-[var(--text-tertiary)] whitespace-nowrap bg-[var(--surface-hover)] px-1.5 py-0.5 rounded">
                   {format(new Date(log.created_at), 'dd/MM/yy HH:mm')}
                 </span>
               </div>
               {log.status === 'exhausted' && log.error && (
                 <div className="text-[10px] text-red-400 bg-red-950/30 p-1.5 rounded mt-1 overflow-x-auto truncate">
                   {log.error}
                 </div>
               )}
             </div>
          ))}
        </div>
      )}
    </div>
  );
}
