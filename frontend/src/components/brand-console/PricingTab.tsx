// S22-14 — Tab 5 Pricing: flujo PriceListVersion (Upload → Preview → Confirm → Activar/Extinguir)
"use client";

import React, { useState, useEffect } from 'react';
import { Upload, CheckCircle, XCircle, Clock, AlertTriangle } from 'lucide-react';
import { PriceListVersionCard } from '@/components/pricing/PriceListVersionCard';
import { UploadPreviewModal } from '@/components/pricing/UploadPreviewModal';
import { GradeItemsTable } from '@/components/pricing/GradeItemsTable';
import { getPriceListVersions, activatePriceList, PriceListVersion } from '@/api/pricing';

export function PricingTab({ brandId }: { brandId?: number }) {
  const [versions, setVersions] = useState<PriceListVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [activating, setActivating] = useState<number | null>(null);

  const fetchVersions = React.useCallback(async () => {
    if (!brandId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const data = await getPriceListVersions(brandId);
      setVersions(data);
    } catch (error) {
      console.error("Error fetching versions:", error);
    } finally {
      setLoading(false);
    }
  }, [brandId]);

  useEffect(() => {
    fetchVersions();
  }, [fetchVersions]);

  const handleActivate = async (versionId: number, force = false) => {
    setActivating(versionId);
    try {
      await activatePriceList(versionId, force);
      await fetchVersions();
    } catch (error) {
      console.error("Error activating version:", error);
      alert("Error al activar: " + (error as any).response?.data?.detail || "Error desconocido");
    } finally {
      setActivating(null);
    }
  };

  const handleUploadConfirm = () => {
    fetchVersions();
    setShowUpload(false);
  };

  if (!brandId) {
    return (
      <div className="card p-12 text-center text-text-tertiary">
        <p className="text-sm">No se ha seleccionado una marca.</p>
      </div>
    );
  }

  const activeVersions = versions.filter((v) => v.is_active);
  const pendingVersions = versions.filter((v) => !v.is_active && !v.activated_at);
  const historicVersions = versions.filter((v) => !v.is_active && v.activated_at);

  if (loading) {
    return <div className="p-10 text-center text-text-tertiary animate-pulse text-xs">Cargando versiones...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="heading-lg">Pricelists</h2>
          <p className="text-xs text-text-tertiary mt-0.5">Gestiona versiones de lista de precios y su activación.</p>
        </div>
        <button
          onClick={() => setShowUpload(true)}
          className="btn btn-primary btn-sm flex items-center gap-2"
        >
          <Upload size={14} />
          Subir nueva versión
        </button>
      </div>

      {activeVersions.length > 1 && (
        <div className="flex items-start gap-2 rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-xs text-amber-800">
          <AlertTriangle size={14} className="mt-0.5 shrink-0" />
          <span>
            Hay <strong>{activeVersions.length} versiones activas simultáneamente</strong>. El engine toma el precio mínimo entre ellas.
          </span>
        </div>
      )}

      {activeVersions.length > 0 && (
        <section>
          <h3 className="text-xs font-semibold text-text-tertiary uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <CheckCircle size={12} className="text-emerald-600" /> Activas ({activeVersions.length})
          </h3>
          <div className="space-y-3">
            {activeVersions.map((v) => (
              <PriceListVersionCard
                key={v.id}
                version={v}
                expanded={expandedId === v.id}
                onToggleExpand={() => setExpandedId(expandedId === v.id ? null : v.id)}
                activating={activating === v.id}
                onDeactivate={() => handleActivate(v.id, true)}
              >
                {expandedId === v.id && <GradeItemsTable versionId={v.id} />}
              </PriceListVersionCard>
            ))}
          </div>
        </section>
      )}

      {pendingVersions.length > 0 && (
        <section>
          <h3 className="text-xs font-semibold text-text-tertiary uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <Clock size={12} className="text-amber-500" /> Pendientes ({pendingVersions.length})
          </h3>
          <div className="space-y-3">
            {pendingVersions.map((v) => (
              <PriceListVersionCard
                key={v.id}
                version={v}
                expanded={expandedId === v.id}
                onToggleExpand={() => setExpandedId(expandedId === v.id ? null : v.id)}
                activating={activating === v.id}
                onActivate={() => handleActivate(v.id, false)}
              >
                {expandedId === v.id && <GradeItemsTable versionId={v.id} />}
              </PriceListVersionCard>
            ))}
          </div>
        </section>
      )}

      {historicVersions.length > 0 && (
        <section>
          <h3 className="text-xs font-semibold text-text-tertiary uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <XCircle size={12} className="text-text-tertiary" /> Historial ({historicVersions.length})
          </h3>
          <div className="space-y-3">
            {historicVersions.map((v) => (
              <PriceListVersionCard
                key={v.id}
                version={v}
                expanded={expandedId === v.id}
                onToggleExpand={() => setExpandedId(expandedId === v.id ? null : v.id)}
                activating={false}
              >
                {expandedId === v.id && <GradeItemsTable versionId={v.id} />}
              </PriceListVersionCard>
            ))}
          </div>
        </section>
      )}

      {showUpload && (
        <UploadPreviewModal
          brandId={brandId}
          onClose={() => setShowUpload(false)}
          onConfirm={handleUploadConfirm}
        />
      )}
    </div>
  );
}
