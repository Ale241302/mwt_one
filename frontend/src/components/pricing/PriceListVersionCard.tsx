// S22-14 — Tarjeta de versión de pricelist
"use client";

import React from 'react';
import { ChevronDown, ChevronUp, Zap, Ban, Clock, CheckCircle, User } from 'lucide-react';
import type { PriceListVersion } from '@/api/pricing';

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
    ? 'border-emerald-200 bg-emerald-50/20 shadow-sm shadow-emerald-100/50'
    : !version.activated_at
    ? 'border-amber-200 bg-amber-50/20 shadow-sm shadow-amber-100/50'
    : 'border-border bg-white grayscale-[0.3] opacity-80 transition-opacity hover:opacity-100';

  return (
    <div className={`rounded-xl border ${statusColor} overflow-hidden transition-all duration-200 ease-in-out`}>
      <div className="flex items-center justify-between px-5 py-4">
        {/* Izquierda: label + metadata */}
        <div className="flex items-center gap-4 min-w-0">
          <div className="shrink-0">
            {version.is_active ? (
              <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600 border border-emerald-200 animate-pulse">
                <CheckCircle size={20} />
              </div>
            ) : !version.activated_at ? (
              <div className="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center text-amber-500 border border-amber-200">
                <Clock size={20} />
              </div>
            ) : (
              <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-text-tertiary border border-border">
                <Ban size={20} />
              </div>
            )}
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <p className="text-sm font-bold text-navy uppercase tracking-tight truncate">{version.version_label}</p>
              {version.is_active && (
                <span className="px-2 py-0.5 bg-emerald-100 text-emerald-700 text-[9px] font-black uppercase rounded-full tracking-wider border border-emerald-200">
                   En producción
                </span>
              )}
            </div>
            <div className="flex items-center gap-2 mt-1 text-[11px] text-text-tertiary font-medium">
              <span className="flex items-center gap-1"><Box size={12} /> {version.items_count} ítems</span>
              <span className="text-border">|</span>
              <span className="flex items-center gap-1"><User size={12} /> {version.uploaded_by_name || 'Desconocido'}</span>
              <span className="text-border">|</span>
              <span className="tabular-nums">{new Date(version.created_at).toLocaleDateString('es-CO')}</span>
            </div>
            {version.notes && (
              <p className="text-[10px] text-text-secondary mt-1.5 italic line-clamp-1 border-l-2 border-brand/20 pl-2">{version.notes}</p>
            )}
          </div>
        </div>

        {/* Derecha: acciones */}
        <div className="flex items-center gap-3 ml-4 shrink-0">
          {onActivate && !version.is_active && !version.activated_at && (
            <button
              onClick={onActivate}
              disabled={activating}
              className="btn btn-sm btn-primary h-9 flex items-center gap-2 px-4 shadow-sm"
            >
              <Zap size={14} className={activating ? 'animate-bounce' : ''} />
              <span className="text-[11px] font-bold uppercase tracking-wide">
                {activating ? 'Activando...' : 'Activar'}
              </span>
            </button>
          )}
          {onDeactivate && version.is_active && (
            <button
              onClick={onDeactivate}
              disabled={activating}
              className="btn btn-sm bg-white text-red-600 border border-red-200 hover:bg-red-50 h-9 flex items-center gap-2 px-4"
            >
              <Ban size={14} />
              <span className="text-[11px] font-bold uppercase tracking-wide">
                 Extinguir
              </span>
            </button>
          )}
          <button
            onClick={onToggleExpand}
            className={`btn btn-sm ${expanded ? 'bg-navy text-white hover:bg-navy/90' : 'btn-ghost text-text-tertiary'} p-2 rounded-lg transition-colors`}
            aria-label={expanded ? 'Colapsar' : 'Ver ítems'}
          >
            {expanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
          </button>
        </div>
      </div>

      {/* Grade items expandibles */}
      {expanded && (
        <div className="border-t border-border bg-bg-alt/5 p-4 animate-in fade-in slide-in-from-top-2 duration-300">
          {children}
        </div>
      )}
    </div>
  );
}
