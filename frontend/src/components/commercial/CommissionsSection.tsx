// S23-13 — CommissionsSection: gestión de CommissionRules (solo visible para CEO)
"use client";

import React, { useState } from 'react';
import {
  Plus, Trash2, AlertCircle, Lock, DollarSign, ChevronDown, ChevronUp
} from 'lucide-react';

// ─── Tipos ────────────────────────────────────────────────────────────────────
type CommissionType = 'percentage' | 'fixed_amount';
type CommissionScope = 'brand' | 'client' | 'subsidiary';
type CommissionBase = 'sale_price' | 'gross_margin' | null;

interface CommissionRule {
  id: string;
  scope: CommissionScope;
  scope_label: string;
  product_key: string | null;
  commission_type: CommissionType;
  commission_value: string;
  commission_base: CommissionBase;
  is_active: boolean;
}

const SCOPE_BADGE: Record<CommissionScope, string> = {
  brand:      'bg-violet-50 text-violet-700 border-violet-200',
  client:     'bg-sky-50 text-sky-700 border-sky-200',
  subsidiary: 'bg-teal-50 text-teal-700 border-teal-200',
};

// ─── Mock data — reemplazar con fetch a /api/commercial/commission-rules/ ─────
const MOCK_RULES: CommissionRule[] = [
  {
    id: 'cr-1',
    scope: 'brand',
    scope_label: 'Marluvas (Brand default)',
    product_key: null,
    commission_type: 'percentage',
    commission_value: '5.00',
    commission_base: null, // DEC-S23-03 pendiente
    is_active: true,
  },
  {
    id: 'cr-2',
    scope: 'client',
    scope_label: 'Calzados del Norte S.A.',
    product_key: 'BOOT-PRO-2026',
    commission_type: 'percentage',
    commission_value: '7.50',
    commission_base: 'sale_price',
    is_active: true,
  },
  {
    id: 'cr-3',
    scope: 'subsidiary',
    scope_label: 'Distribuidora Sur — Bogotá',
    product_key: null,
    commission_type: 'fixed_amount',
    commission_value: '120.00',
    commission_base: null,
    is_active: false,
  },
];

interface Props {
  userRole: string;
}

export function CommissionsSection({ userRole }: Props) {
  const [rules] = useState<CommissionRule[]>(MOCK_RULES);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // S23-13: solo CEO puede ver comisiones — si no es CEO, no renderizar nada
  if (userRole !== 'CEO') {
    return (
      <div className="card p-10 text-center">
        <Lock size={32} className="mx-auto mb-3 opacity-20 text-text-tertiary" />
        <p className="text-sm text-text-tertiary">Esta sección es solo visible para el CEO.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="heading-lg">Reglas de Comisión</h2>
          <p className="text-xs text-text-tertiary mt-0.5">
            Configuración de comisiones por agente. Scope: brand → client → subsidiary.
            Visible únicamente para CEO.
          </p>
        </div>
        <button
          className="btn btn-primary btn-sm flex items-center gap-2"
          title="Alta de regla — conectar a POST /api/commercial/commission-rules/"
        >
          <Plus size={14} /> Nueva regla
        </button>
      </div>

      {/* Tabla de reglas */}
      {rules.length === 0 ? (
        <div className="card p-10 text-center">
          <DollarSign size={36} className="mx-auto mb-3 opacity-20 text-text-tertiary" />
          <p className="text-sm text-text-tertiary">No hay reglas de comisión configuradas.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {rules.map((rule) => (
            <div key={rule.id} className="card overflow-hidden">
              <div className="flex items-center justify-between px-5 py-4">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${rule.is_active ? 'bg-emerald-500' : 'bg-text-tertiary'}`} />
                  <div>
                    <div className="flex items-center gap-2">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded border text-[10px] font-semibold ${SCOPE_BADGE[rule.scope]}`}
                      >
                        {rule.scope.toUpperCase()}
                      </span>
                      <p className="text-sm font-semibold text-text-primary">{rule.scope_label}</p>
                    </div>
                    <p className="text-xs text-text-tertiary mt-0.5">
                      {rule.product_key
                        ? <span>Producto: <code className="font-mono bg-bg-alt px-1 rounded">{rule.product_key}</code></span>
                        : 'Todos los productos (default)'}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <p className="text-sm font-bold text-text-primary tabular-nums">
                      {rule.commission_type === 'percentage'
                        ? `${rule.commission_value}%`
                        : `USD ${rule.commission_value}`}
                    </p>
                    <p className="text-[10px] text-text-tertiary">
                      {rule.commission_base ?? <span className="text-amber-600">base pendiente</span>}
                    </p>
                  </div>
                  <button
                    onClick={() => setExpandedId(expandedId === rule.id ? null : rule.id)}
                    className="btn btn-ghost btn-sm p-2"
                  >
                    {expandedId === rule.id ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  </button>
                  <button className="btn btn-ghost btn-sm p-2 text-red-400 hover:bg-red-50" title="Eliminar regla">
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>

              {expandedId === rule.id && (
                <div className="border-t border-border px-5 py-4 grid grid-cols-2 gap-4 text-xs">
                  <div>
                    <p className="text-text-tertiary mb-1">Tipo</p>
                    <p className="font-medium text-text-primary capitalize">{rule.commission_type.replace('_', ' ')}</p>
                  </div>
                  <div>
                    <p className="text-text-tertiary mb-1">Base de cálculo</p>
                    <p className={`font-medium ${rule.commission_base ? 'text-text-primary' : 'text-amber-600'}`}>
                      {rule.commission_base ?? 'No definido (DEC-S23-03)'}
                    </p>
                  </div>
                  <div>
                    <p className="text-text-tertiary mb-1">Estado</p>
                    <p className={`font-medium ${rule.is_active ? 'text-emerald-600' : 'text-text-tertiary'}`}>
                      {rule.is_active ? 'Activo' : 'Inactivo'}
                    </p>
                  </div>
                  <div>
                    <p className="text-text-tertiary mb-1">Scope</p>
                    <p className="font-medium text-text-primary capitalize">{rule.scope}</p>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Nota DEC-S23-03 */}
      <div className="flex items-start gap-2 p-3 rounded-lg border border-amber-200 bg-amber-50 text-xs text-amber-800">
        <AlertCircle size={14} className="mt-0.5 shrink-0" />
        <p>
          <span className="font-semibold">DEC-S23-03 pendiente:</span> El campo{' '}
          <code className="font-mono bg-amber-100 px-1 rounded">commission_base</code>{' '}
          está en NULL hasta resolución del CEO. El backend lanzará{' '}
          <code className="font-mono bg-amber-100 px-1 rounded">ValueError</code>{' '}
          al intentar calcular comisiones con base NULL.
        </p>
      </div>
    </div>
  );
}
