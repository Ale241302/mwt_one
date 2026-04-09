"use client";

import { format } from "date-fns";

type Log = {
  id: string;
  template_key: string;
  expediente_code: string;
  recipient_email: string;
  subject: string;
  created_at: string;
  completed_at: string | null;
  status: string;
  error: string;
  attempt_count: number;
};

interface Props {
  logs: Log[];
  loading: boolean;
}

export function NotificationLogTable({ logs, loading }: Props) {
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'sent': return <span className="px-2 py-1 text-[10px] uppercase rounded-full bg-mint-soft/20 text-mint font-bold border border-mint/20">Sent</span>;
      case 'skipped': return <span className="px-2 py-1 text-[10px] uppercase rounded-full bg-bg border border-border text-text-tertiary font-bold">Skipped</span>;
      case 'disabled': return <span className="px-2 py-1 text-[10px] uppercase rounded-full bg-amber/10 text-amber font-bold border border-amber/20">Disabled</span>;
      case 'exhausted': return <span className="px-2 py-1 text-[10px] uppercase rounded-full bg-coral-soft/20 text-coral font-bold border border-coral/20">Exhausted</span>;
      default: return <span className="px-2 py-1 text-[10px] uppercase rounded-full bg-surface border border-border text-text-secondary font-bold">{status}</span>;
    }
  };

  return (
    <div className="bg-surface rounded-xl shadow-sm border border-border overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse whitespace-nowrap">
          <thead>
            <tr className="bg-bg-alt/50 text-xs uppercase text-text-tertiary font-semibold tracking-wider border-b border-border">
            <th className="px-5 py-4">Fecha / Status</th>
            <th className="px-5 py-4">Expediente</th>
            <th className="px-5 py-4">Template / Asunto</th>
            <th className="px-5 py-4">Destinatario</th>
            <th className="px-5 py-4">Detalle Error</th>
          </tr>
        </thead>
        <tbody>
          {loading && logs.length === 0 ? (
             <tr><td colSpan={5} className="px-5 py-8 text-center text-text-tertiary">Cargando...</td></tr>
          ) : logs.map((log, idx) => (
            <tr key={log.id} className={`group cursor-pointer transition-colors border-b border-divider hover:bg-surface-hover ${idx % 2 === 0 ? 'bg-surface' : 'bg-bg-alt/30'}`}>
              <td className="px-5 py-4">
                <div className="text-sm font-medium text-text-primary whitespace-nowrap group-hover:text-mint transition-colors">{format(new Date(log.created_at), 'dd/MM/yyyy HH:mm')}</div>
                <div className="mt-2">{getStatusBadge(log.status)}</div>
              </td>
              <td className="px-5 py-4 font-medium text-text-secondary">
                {log.expediente_code || 'N/A'}
              </td>
              <td className="px-5 py-4 max-w-xs truncate" title={log.subject}>
                <div className="text-mint font-medium text-xs mb-1">{log.template_key}</div>
                <div className="text-text-secondary text-sm">{log.subject}</div>
              </td>
              <td className="px-5 py-4 font-medium text-text-secondary text-sm">
                {log.recipient_email}
              </td>
              <td className="px-5 py-4 text-xs text-coral max-w-xs truncate" title={log.error}>
                {log.error || '-'}
              </td>
            </tr>
          ))}
          {!loading && logs.length === 0 && (
            <tr>
              <td colSpan={5} className="px-5 py-12 text-center text-text-tertiary bg-surface">
                No hay registros de notificaciones.
              </td>
            </tr>
          )}
         </tbody>
      </table>
      </div>
    </div>
  );
}
