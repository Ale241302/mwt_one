// S22-14 — Tarjeta de versión de pricelist
"use client";

import React from 'react';
import { ChevronDown, ChevronUp, Zap, Ban, Clock, CheckCircle } from 'lucide-react';
import type { PriceListVersion } from '@/components/brand-console/PricingTab';

const DEACTIVATION_LABELS: Record<string, string> = {
  manual: 'Desactivada manualmente',
  price_decrease: 'Precio menor detectado',
  superseded: 'Reemplazada por versión nueva',
};

interface Props {
  version: PriceListVersion;
  expanded: boolean;
  onToggleExpand: () => void;
  activating: boolean;
  onActivate?: () => void;
  onDeactivate?: () => void;
  children?: React.ReactNode;
}

export function PriceListVersionCard({
  version,
  expanded,
  onToggleExpand,
  activating,
  onActivate,
  onDeactivate,
  children,
}: Props) {
  const statusColor = version.is_active
    ? 'border-emerald-300 bg-emerald-50/40'
    : !version.deactivated_at
    ? 'border-amber-300 bg-amber-50/40'
    : 'border-border bg-white';

  return (
    <div className={`rounded-xl border ${statusColor} overflow-hidden transition-all`}>
      <div className="flex items-center justify-between px-5 py-4">
        {/* Izquierda: label + metadata */}
        <div className="flex items-center gap-3 min-w-0">
          <div>
            {version.is_active ? (
              <CheckCircle size={16} className="text-emerald-600" />
            ) : !version.deactivated_at ? (
              <Clock size={16} className="text-amber-500" />
            ) : (
              <Ban size={16} className="text-text-tertiary" />
            )}
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-text-primary truncate">{version.version_label}</p>
            <p className="text-xs text-text-tertiary mt-0.5">
              {version.items_count} ítems · Subido por {version.uploaded_by}
              {version.is_active && version.activated_at && (
                <> · Activa desde {new Date(version.activated_at).toLocaleDateString('es-CO')}</>
              )}
              {!version.is_active && version.deactivated_at && (
                <> · {DEACTIVATION_LABELS[version.deactivation_reason ?? ''] ?? 'Extinguida'} el {new Date(version.deactivated_at).toLocaleDateString('es-CO')}</>
              )}
            </p>
            {version.notes && (
              <p className="text-xs text-text-secondary mt-0.5 italic">{version.notes}</p>
            )}
          </div>
        </div>

        {/* Derecha: acciones */}
        <div className="flex items-center gap-2 ml-4 shrink-0">
          {onActivate && !version.is_active && !version.deactivated_at && (
            <button
              onClick={onActivate}
              disabled={activating}
              className="btn btn-sm btn-primary flex items-center gap-1.5 disabled:opacity-60"
            >
              <Zap size={13} />
              {activating ? 'Activando...' : 'Activar'}
            </button>
          )}
          {onDeactivate && version.is_active && (
            <button
              onClick={onDeactivate}
              disabled={activating}
              className="btn btn-sm btn-secondary text-red-600 border-red-300 hover:bg-red-50 flex items-center gap-1.5 disabled:opacity-60"
            >
              <Ban size={13} />
              {activating ? 'Extinguiendo...' : 'Extinguir'}
            </button>
          )}
          <button
            onClick={onToggleExpand}
            className="btn btn-sm btn-ghost p-2"
            aria-label={expanded ? 'Colapsar' : 'Ver ítems'}
          >
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
        </div>
      </div>

      {/* Grade items expandibles */}
      {expanded && (
        <div className="border-t border-border">
          {children}
        </div>
      )}
    </div>
  );
}
