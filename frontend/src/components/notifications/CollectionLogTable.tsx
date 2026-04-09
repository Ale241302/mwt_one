"use client";

import { format } from "date-fns";

type CollectionLog = {
  id: string;
  expediente_code: string;
  recipient_email: string;
  amount_overdue: string;
  grace_days_used: number;
  created_at: string;
  completed_at: string | null;
  status: string;
  error: string;
};

interface Props {
  logs: CollectionLog[];
  loading: boolean;
}

export function CollectionLogTable({ logs, loading }: Props) {
  const getStatusBadge = (status: string) => {
    if (status === 'sent') return <span className="px-2 py-1 text-[10px] uppercase rounded-full bg-[rgba(117,203,179,0.15)] text-mint font-bold">Sent</span>;
    if (status === 'failed') return <span className="px-2 py-1 text-[10px] uppercase rounded-full bg-red-500/20 text-red-400 font-bold">Failed</span>;
    return <span className="px-2 py-1 text-[10px] uppercase rounded-full bg-[rgba(255,255,255,0.1)] text-white font-bold">{status}</span>;
  };

  return (
    <div className="bg-navy overflow-hidden">
      <table className="w-full text-sm text-left text-[rgba(255,255,255,0.8)]">
        <thead className="text-xs uppercase bg-navy-dark text-[rgba(255,255,255,0.6)] border-b border-[rgba(255,255,255,0.1)]">
          <tr>
            <th className="px-6 py-4 font-semibold">Fecha / Status</th>
            <th className="px-6 py-4 font-semibold">Expediente</th>
            <th className="px-6 py-4 font-semibold">Destinatario</th>
            <th className="px-6 py-4 font-semibold">Monto / Gracia</th>
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
              <td className="px-6 py-4 font-medium">
                {log.recipient_email}
              </td>
              <td className="px-6 py-4">
                <div className="text-mint font-medium font-mono">${log.amount_overdue}</div>
                <div className="text-xs text-[rgba(255,255,255,0.6)] mt-1">{log.grace_days_used} días gracia</div>
              </td>
              <td className="px-6 py-4 text-xs text-red-300 max-w-xs truncate" title={log.error}>
                {log.error || '-'}
              </td>
            </tr>
          ))}
          {!loading && logs.length === 0 && (
            <tr>
              <td colSpan={5} className="px-6 py-8 text-center text-[rgba(255,255,255,0.5)]">
                No hay registros de cobranza.
              </td>
            </tr>
          )}
         </tbody>
      </table>
    </div>
  );
}
