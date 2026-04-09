"use client";

import { useState, useEffect, useCallback } from "react";
import api from "@/lib/api";
import { CollectionLogTable } from "@/components/notifications/CollectionLogTable";

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

export default function CollectionsLogPage() {
  const [logs, setLogs] = useState<CollectionLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get(`/notifications/collections/?page=${page}`);
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
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Historial de Cobranza Automática</h1>
          <p className="text-[rgba(255,255,255,0.6)] mt-2">
            Registro inmutable de correos de pagos vencidos generados por cron.
          </p>
        </div>
      </div>

      <CollectionLogTable logs={logs} loading={loading} />

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
