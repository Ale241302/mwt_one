// S22-17 — Tab 9: Assignments — CPAs por cliente con bulk assign y stale indicator
"use client";

import React, { useState, useEffect } from 'react';
import { RefreshCw, AlertCircle, Package, Plus } from 'lucide-react';
import { BulkAssignModal } from '@/components/assignments/BulkAssignModal';
import { getClientAssignments, ClientProductAssignment } from '@/api/pricing';

export function AssignmentsTab({ brandId }: { brandId?: string | number }) {
  const [assignments, setAssignments] = useState<ClientProductAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [showBulkAssign, setShowBulkAssign] = useState(false);
  const [recalculating, setRecalculating] = useState<number | null>(null);
  const [filterStale, setFilterStale] = useState(false);

  const fetchAssignments = React.useCallback(async () => {
    if (!brandId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const data = await getClientAssignments(brandId);
      setAssignments(data);
    } catch (error) {
      console.error("Error fetching assignments:", error);
    } finally {
      setLoading(false);
    }
  }, [brandId]);

  useEffect(() => {
    fetchAssignments();
  }, [fetchAssignments]);

  const handleRecalculate = async (id: number) => {
    setRecalculating(id);
    try {
      await new Promise((r) => setTimeout(r, 800));
      await fetchAssignments();
    } catch (error) {
      console.error("Error recalculating:", error);
    } finally {
      setRecalculating(null);
    }
  };

  const handleBulkAssignCreated = () => {
    fetchAssignments();
    setShowBulkAssign(false);
  };

  if (!brandId) {
    return (
      <div className="card p-12 text-center text-text-tertiary">
        <p className="text-sm">No se ha seleccionado una marca.</p>
      </div>
    );
  }

  const staleCount = assignments.filter((a) => a.is_stale).length;
  const displayed = filterStale ? assignments.filter((a) => a.is_stale) : assignments;

  if (loading) {
    return <div className="p-10 text-center text-text-tertiary animate-pulse text-xs">Cargando assignments...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="heading-lg">Assignments (CPAs)</h2>
          <p className="text-xs text-text-tertiary mt-0.5">Precios cacheados por cliente × SKU. El recálculo usa skip_cache=True.</p>
        </div>
        <button
          onClick={() => setShowBulkAssign(true)}
          className="btn btn-primary btn-sm flex items-center gap-2"
        >
          <Plus size={14} /> Bulk Assign
        </button>
      </div>

      {staleCount > 0 && (
        <div className="flex items-center justify-between rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-xs text-amber-800">
          <div className="flex items-center gap-2">
            <AlertCircle size={14} />
            <span><strong>{staleCount} assignments</strong> tienen precio desactualizado (cached_at {'>'} 7 días).</span>
          </div>
          <button
            onClick={() => setFilterStale((f) => !f)}
            className="text-amber-700 font-semibold underline underline-offset-2"
          >
            {filterStale ? 'Ver todos' : 'Ver solo stale'}
          </button>
        </div>
      )}

      <div className="table-container">
        <table className="text-xs">
          <thead>
            <tr>
              <th>Cliente</th>
              <th>SKU</th>
              <th>Descripción</th>
              <th className="text-right">Precio cliente</th>
              <th className="text-right">Precio base</th>
              <th>Cacheado</th>
              <th>Estado</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {displayed.map((a) => (
              <tr key={a.id} className={a.is_stale ? 'bg-amber-50/40' : ''}>
                <td className="font-medium">{a.client_subsidiary_name}</td>
                <td className="font-mono">{a.brand_sku_code}</td>
                <td className="text-text-secondary">{a.brand_sku_description}</td>
                <td className="text-right font-mono font-semibold">${a.cached_client_price}</td>
                <td className="text-right font-mono text-text-secondary">${a.cached_base_price}</td>
                <td className="text-text-tertiary">
                  {a.cached_at ? new Date(a.cached_at).toLocaleDateString('es-CO') : 'Nunca'}
                  {a.is_stale && (
                    <span className="ml-1.5 inline-flex items-center gap-0.5 rounded-full bg-amber-100 text-amber-700 px-1.5 py-0.5 text-[10px] font-semibold">
                      <AlertCircle size={9} /> stale
                    </span>
                  )}
                </td>
                <td>
                  <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                    a.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-[var(--bg-alt)] text-text-tertiary'
                  }`}>
                    {a.is_active ? 'Activo' : 'Inactivo'}
                  </span>
                </td>
                <td>
                  <button
                    onClick={() => handleRecalculate(a.id)}
                    disabled={recalculating === a.id}
                    className="btn btn-ghost btn-sm p-1.5 text-text-tertiary hover:text-brand disabled:opacity-50"
                    title="Recalcular precio (skip_cache=True)"
                  >
                    <RefreshCw size={13} className={recalculating === a.id ? 'animate-spin' : ''} />
                  </button>
                </td>
              </tr>
            ))}
            {displayed.length === 0 && (
              <tr>
                <td colSpan={8} className="text-center py-10 text-text-tertiary">
                  <Package size={28} className="mx-auto mb-2 opacity-20" />
                  Sin assignments{filterStale ? ' stale' : ''} para esta marca.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {showBulkAssign && (
        <BulkAssignModal
          brandId={brandId}
          onClose={() => setShowBulkAssign(false)}
          onCreated={handleBulkAssignCreated}
        />
      )}
    </div>
  );
}
