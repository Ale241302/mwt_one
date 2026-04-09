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
      case 'sent': return <span className="px-2 py-1 text-[10px] uppercase rounded-full bg-[rgba(117,203,179,0.15)] text-mint font-bold">Sent</span>;
      case 'skipped': return <span className="px-2 py-1 text-[10px] uppercase rounded-full bg-[rgba(255,255,255,0.1)] text-[rgba(255,255,255,0.6)] font-bold">Skipped</span>;
      case 'disabled': return <span className="px-2 py-1 text-[10px] uppercase rounded-full bg-yellow-500/20 text-yellow-400 font-bold">Disabled</span>;
      case 'exhausted': return <span className="px-2 py-1 text-[10px] uppercase rounded-full bg-red-500/20 text-red-400 font-bold">Exhausted</span>;
      default: return <span className="px-2 py-1 text-[10px] uppercase rounded-full bg-[rgba(255,255,255,0.1)] text-white font-bold">{status}</span>;
    }
  };

  return (
    <div className="bg-navy overflow-hidden">
      <table className="w-full text-sm text-left text-[rgba(255,255,255,0.8)]">
        <thead className="text-xs uppercase bg-navy-dark text-[rgba(255,255,255,0.6)] border-b border-[rgba(255,255,255,0.1)]">
          <tr>
            <th className="px-6 py-4 font-semibold">Fecha / Status</th>
            <th className="px-6 py-4 font-semibold">Expediente</th>
            <th className="px-6 py-4 font-semibold">Template / Asunto</th>
            <th className="px-6 py-4 font-semibold">Destinatario</th>
            <th className="px-6 py-4 font-semibold">Detalle Error</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[rgba(255,255,255,0.06)]">
          {loading && logs.length === 0 ? (
             <tr><td colSpan={5} className="px-6 py-8 text-center text-[rgba(255,255,255,0.5)]">Cargando...</td></tr>
          ) : logs.map((log) => (
            <tr key={log.id} className="hover:bg-[rgba(255,255,255,0.02)] transition-colors">
              <td className="px-6 py-4">
                <div className="text-white whitespace-nowrap">{format(new Date(log.created_at), 'dd/MM/yyyy HH:mm')}</div>
                <div className="mt-2">{getStatusBadge(log.status)}</div>
              </td>
              <td className="px-6 py-4 font-medium text-white">
                {log.expediente_code || 'N/A'}
              </td>
              <td className="px-6 py-4 max-w-xs truncate" title={log.subject}>
                <div className="text-mint font-medium text-xs mb-1">{log.template_key}</div>
                <div className="text-[rgba(255,255,255,0.7)]">{log.subject}</div>
              </td>
              <td className="px-6 py-4 font-medium">
                {log.recipient_email}
              </td>
              <td className="px-6 py-4 text-xs text-red-300 max-w-xs truncate" title={log.error}>
                {log.error || '-'}
              </td>
            </tr>
          ))}
          {!loading && logs.length === 0 && (
            <tr>
              <td colSpan={5} className="px-6 py-8 text-center text-[rgba(255,255,255,0.5)]">
                No hay registros de notificaciones.
              </td>
            </tr>
          )}
         </tbody>
      </table>
    </div>
  );
}
