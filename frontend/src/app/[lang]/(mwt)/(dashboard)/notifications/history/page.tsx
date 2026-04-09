"use client";

import { useState, useEffect, useCallback } from "react";
import api from "@/lib/api";
import { NotificationLogTable } from "@/components/notifications/NotificationLogTable";

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

export default function HistoryPage() {
  const [logs, setLogs] = useState<Log[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get(`/notifications/log/?page=${page}`);
      setLogs(res.data.results);
      setTotalCount(res.data.count);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-display font-bold">Historial de Notificaciones</h1>
          <p className="text-sm text-text-tertiary mt-1">
            Registro inmutable terminal de emails transaccionales enviados.
          </p>
        </div>
      </div>

      <NotificationLogTable logs={logs} loading={loading} />

      {/* Pagination */}
      <div className="p-4 border-t border-[rgba(255,255,255,0.06)] flex justify-between items-center text-sm text-[rgba(255,255,255,0.6)]">
        <div>Mostrando página {page} de {Math.ceil(totalCount / 25) || 1} ({totalCount} total)</div>
        <div className="flex space-x-2">
          <button
            disabled={page === 1}
            onClick={() => setPage(p => p - 1)}
            className="px-3 py-1 bg-[rgba(255,255,255,0.05)] hover:bg-[rgba(255,255,255,0.1)] rounded disabled:opacity-50"
          >
            Anterior
          </button>
          <button
            disabled={page * 25 >= totalCount}
            onClick={() => setPage(p => p + 1)}
            className="px-3 py-1 bg-[rgba(255,255,255,0.05)] hover:bg-[rgba(255,255,255,0.1)] rounded disabled:opacity-50"
          >
            Siguiente
          </button>
        </div>
      </div>
    </div>
  );
}
