// S22-14 — Tab 5 Pricing: flujo PriceListVersion (Upload → Preview → Confirm → Activar/Extinguir)
"use client";

import React, { useState } from 'react';
import { Upload, CheckCircle, XCircle, Clock, ChevronDown, ChevronUp, Zap, AlertTriangle } from 'lucide-react';
import { PriceListVersionCard } from '@/components/pricing/PriceListVersionCard';
import { UploadPreviewModal } from '@/components/pricing/UploadPreviewModal';
import { GradeItemsTable } from '@/components/pricing/GradeItemsTable';

export interface PriceListVersion {
  id: number;
  version_label: string;
  is_active: boolean;
  activated_at: string | null;
  deactivated_at: string | null;
  deactivation_reason: 'manual' | 'price_decrease' | 'superseded' | null;
  uploaded_by: string;
  notes: string;
  items_count: number;
}

// Mock data — reemplazar con llamada real a /api/pricing/pricelists/
const MOCK_VERSIONS: PriceListVersion[] = [
  {
    id: 3,
    version_label: 'Marluvas Q2-2026',
    is_active: true,
    activated_at: '2026-04-01T10:00:00Z',
    deactivated_at: null,
    deactivation_reason: null,
    uploaded_by: 'admin@mwt.com',
    notes: 'Actualización trimestral con nuevos grades',
    items_count: 142,
  },
  {
    id: 2,
    version_label: 'Marluvas Q1-2026',
    is_active: false,
    activated_at: '2026-01-05T08:00:00Z',
    deactivated_at: '2026-04-01T10:00:00Z',
    deactivation_reason: 'superseded',
    uploaded_by: 'admin@mwt.com',
    notes: '',
    items_count: 138,
  },
  {
    id: 1,
    version_label: 'Marluvas Legacy 2025',
    is_active: false,
    activated_at: '2025-06-01T00:00:00Z',
    deactivated_at: '2026-01-05T08:00:00Z',
    deactivation_reason: 'superseded',
    uploaded_by: 'ceo@mwt.com',
    notes: 'Versión original migrada de Excel',
    items_count: 115,
  },
];

export function PricingTab() {
  const [versions, setVersions] = useState<PriceListVersion[]>(MOCK_VERSIONS);
  const [showUpload, setShowUpload] = useState(false);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [activating, setActivating] = useState<number | null>(null);

  const handleActivate = async (versionId: number, force = false) => {
    setActivating(versionId);
    // TODO: llamar POST /api/pricing/pricelists/{id}/activate/?force=true/false
    await new Promise((r) => setTimeout(r, 900));
    setVersions((prev) =>
      prev.map((v) => ({
        ...v,
        is_active: v.id === versionId,
        deactivated_at: v.is_active && v.id !== versionId ? new Date().toISOString() : v.deactivated_at,
        deactivation_reason: v.is_active && v.id !== versionId ? 'superseded' : v.deactivation_reason,
        activated_at: v.id === versionId ? new Date().toISOString() : v.activated_at,
      }))
    );
    setActivating(null);
  };

  const handleUploadConfirm = (newVersion: PriceListVersion) => {
    setVersions((prev) => [newVersion, ...prev]);
    setShowUpload(false);
  };

  const activeVersions = versions.filter((v) => v.is_active);
  const pendingVersions = versions.filter((v) => !v.is_active && !v.deactivated_at);
  const historicVersions = versions.filter((v) => !v.is_active && v.deactivated_at);

  return (
    <div className="space-y-6">
      {/* Header */}
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

      {/* Alerta versiones activas */}
      {activeVersions.length > 1 && (
        <div className="flex items-start gap-2 rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-xs text-amber-800">
          <AlertTriangle size={14} className="mt-0.5 shrink-0" />
          <span>
            Hay <strong>{activeVersions.length} versiones activas simultáneamente</strong>. El engine toma el precio mínimo entre ellas.
          </span>
        </div>
      )}

      {/* Versiones activas */}
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

      {/* Versiones pendientes (subidas, no activadas) */}
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

      {/* Historial */}
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

      {/* Upload modal */}
      {showUpload && (
        <UploadPreviewModal
          onClose={() => setShowUpload(false)}
          onConfirm={handleUploadConfirm}
        />
      )}
    </div>
  );
}
