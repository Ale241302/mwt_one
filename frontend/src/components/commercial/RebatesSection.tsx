// S23-13 — RebatesSection: CRUD de RebatePrograms + Assignments para Brand Console
"use client";

import React, { useState } from 'react';
import {
  Plus, Trash2, Save, ChevronDown, ChevronUp,
  TrendingUp, Calendar, CheckCircle, XCircle, AlertCircle
} from 'lucide-react';

// ─── Tipos locales (alinear con backend serializers cuando estén listos) ──────
type RebateType = 'percentage' | 'fixed_amount';
type PeriodType = 'monthly' | 'quarterly' | 'semi_annual' | 'annual';
type ThresholdType = 'none' | 'amount' | 'units';
type LedgerStatus = 'accruing' | 'pending_review' | 'liquidated' | 'cancelled';

interface RebateProgram {
  id: string;
  name: string;
  period_type: PeriodType;
  rebate_type: RebateType;
  rebate_value: string;
  threshold_type: ThresholdType;
  threshold_amount: string | null;
  threshold_units: number | null;
  valid_from: string;
  valid_to: string | null;
  is_active: boolean;
}

interface RebateLedger {
  id: string;
  program_name: string;
  client_name: string;
  status: LedgerStatus;
  period_start: string;
  period_end: string;
  accrued_rebate: string;
  entries_count: number;
}

const STATUS_BADGE: Record<LedgerStatus, { label: string; className: string }> = {
  accruing:       { label: 'Acumulando',     className: 'bg-blue-50 text-blue-700 border-blue-200' },
  pending_review: { label: 'Pend. revisión', className: 'bg-amber-50 text-amber-700 border-amber-200' },
  liquidated:     { label: 'Liquidado',      className: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
  cancelled:      { label: 'Cancelado',      className: 'bg-red-50 text-red-700 border-red-200' },
};

const PERIOD_LABELS: Record<PeriodType, string> = {
  monthly:     'Mensual',
  quarterly:   'Trimestral',
  semi_annual: 'Semestral',
  annual:      'Anual',
};

// ─── Mock data — reemplazar con fetch a /api/commercial/rebates/ ──────────────
const MOCK_PROGRAMS: RebateProgram[] = [
  {
    id: 'prog-1',
    name: 'Q1 Volume Rebate 2026',
    period_type: 'quarterly',
    rebate_type: 'percentage',
    rebate_value: '3.50',
    threshold_type: 'amount',
    threshold_amount: '50000.00',
    threshold_units: null,
    valid_from: '2026-01-01',
    valid_to: '2026-12-31',
    is_active: true,
  },
  {
    id: 'prog-2',
    name: 'Annual Fixed Rebate',
    period_type: 'annual',
    rebate_type: 'fixed_amount',
    rebate_value: '1200.00',
    threshold_type: 'units',
    threshold_amount: null,
    threshold_units: 5000,
    valid_from: '2026-01-01',
    valid_to: null,
    is_active: true,
  },
];

const MOCK_LEDGERS: RebateLedger[] = [
  {
    id: 'led-1',
    program_name: 'Q1 Volume Rebate 2026',
    client_name: 'Calzados del Norte S.A.',
    status: 'accruing',
    period_start: '2026-01-01',
    period_end: '2026-03-31',
    accrued_rebate: '1250.00',
    entries_count: 8,
  },
  {
    id: 'led-2',
    program_name: 'Q1 Volume Rebate 2026',
    client_name: 'Distribuidora Sur Ltda.',
    status: 'pending_review',
    period_start: '2026-01-01',
    period_end: '2026-03-31',
    accrued_rebate: '3400.00',
    entries_count: 14,
  },
];

// ─── Sub-vista: Lista de programas ───────────────────────────────────────────
function ProgramsList() {
  const [programs] = useState<RebateProgram[]>(MOCK_PROGRAMS);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  return (
    <div className="space-y-3">
      {programs.length === 0 && (
        <div className="card p-10 text-center">
          <TrendingUp size={36} className="mx-auto mb-3 opacity-20 text-text-tertiary" />
          <p className="text-sm text-text-tertiary">No hay programas de rebate para esta marca.</p>
        </div>
      )}
      {programs.map((prog) => (
        <div key={prog.id} className="card overflow-hidden">
          <div className="flex items-center justify-between px-5 py-4">
            <div className="flex items-center gap-3">
              <div className={`w-2 h-2 rounded-full ${prog.is_active ? 'bg-emerald-500' : 'bg-text-tertiary'}`} />
              <div>
                <p className="text-sm font-semibold text-text-primary">{prog.name}</p>
                <p className="text-xs text-text-tertiary">
                  {PERIOD_LABELS[prog.period_type]} · {prog.rebate_type === 'percentage' ? `${prog.rebate_value}%` : `$${prog.rebate_value}`}
                  {prog.threshold_type !== 'none' && (
                    <span className="ml-2 text-[10px] font-mono bg-bg-alt px-1.5 py-0.5 rounded">
                      umbral {prog.threshold_type === 'amount' ? `$${prog.threshold_amount}` : `${prog.threshold_units} u`}
                    </span>
                  )}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-text-tertiary font-mono">
                {prog.valid_from} → {prog.valid_to ?? '∞'}
              </span>
              <button
                onClick={() => setExpandedId(expandedId === prog.id ? null : prog.id)}
                className="btn btn-ghost btn-sm p-2"
              >
                {expandedId === prog.id ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              </button>
            </div>
          </div>

          {expandedId === prog.id && (
            <div className="border-t border-border px-5 py-4 grid grid-cols-3 gap-4 text-xs">
              <div>
                <p className="text-text-tertiary mb-1">Tipo rebate</p>
                <p className="font-medium text-text-primary capitalize">{prog.rebate_type.replace('_', ' ')}</p>
              </div>
              <div>
                <p className="text-text-tertiary mb-1">Valor</p>
                <p className="font-medium text-text-primary">
                  {prog.rebate_type === 'percentage' ? `${prog.rebate_value}%` : `USD ${prog.rebate_value}`}
                </p>
              </div>
              <div>
                <p className="text-text-tertiary mb-1">Threshold</p>
                <p className="font-medium text-text-primary">
                  {prog.threshold_type === 'none' && 'Sin umbral'}
                  {prog.threshold_type === 'amount' && `≥ $${prog.threshold_amount}`}
                  {prog.threshold_type === 'units' && `≥ ${prog.threshold_units} unidades`}
                </p>
              </div>
              <div className="col-span-3 flex items-center gap-2 pt-2 border-t border-border">
                {prog.is_active
                  ? <CheckCircle size={13} className="text-emerald-500" />
                  : <XCircle size={13} className="text-red-400" />}
                <span className="text-text-secondary">{prog.is_active ? 'Programa activo' : 'Inactivo'}</span>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// ─── Sub-vista: Ledger de accruals ───────────────────────────────────────────
function LedgerList() {
  const [ledgers] = useState<RebateLedger[]>(MOCK_LEDGERS);

  return (
    <div className="space-y-3">
      {ledgers.length === 0 && (
        <div className="card p-10 text-center">
          <Calendar size={36} className="mx-auto mb-3 opacity-20 text-text-tertiary" />
          <p className="text-sm text-text-tertiary">No hay ledgers de rebate activos.</p>
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-border text-text-tertiary">
              <th className="text-left pb-2 font-medium">Programa</th>
              <th className="text-left pb-2 font-medium">Cliente</th>
              <th className="text-left pb-2 font-medium">Período</th>
              <th className="text-right pb-2 font-medium">Accrued</th>
              <th className="text-center pb-2 font-medium">Entradas</th>
              <th className="text-center pb-2 font-medium">Estado</th>
              <th className="text-center pb-2 font-medium">Acción</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {ledgers.map((led) => (
              <tr key={led.id} className="hover:bg-bg-alt/20 transition-colors">
                <td className="py-3 text-text-primary font-medium">{led.program_name}</td>
                <td className="py-3 text-text-secondary">{led.client_name}</td>
                <td className="py-3 text-text-tertiary font-mono">{led.period_start} → {led.period_end}</td>
                <td className="py-3 text-right font-semibold text-text-primary tabular-nums">
                  ${parseFloat(led.accrued_rebate).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </td>
                <td className="py-3 text-center text-text-tertiary">{led.entries_count}</td>
                <td className="py-3 text-center">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded border text-[10px] font-medium ${STATUS_BADGE[led.status].className}`}>
                    {STATUS_BADGE[led.status].label}
                  </span>
                </td>
                <td className="py-3 text-center">
                  {led.status === 'pending_review' && (
                    <button className="btn btn-sm btn-primary text-[10px] px-3">
                      Aprobar
                    </button>
                  )}
                  {led.status === 'accruing' && (
                    <span className="text-text-tertiary text-[10px]">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── Componente principal ─────────────────────────────────────────────────────
export function RebatesSection() {
  const [view, setView] = useState<'programs' | 'ledger'>('programs');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="heading-lg">Programas de Rebate</h2>
          <p className="text-xs text-text-tertiary mt-0.5">
            Incentivos por volumen. Los accruals se calculan automáticamente al cerrar proformas.
          </p>
        </div>
        <button
          className="btn btn-primary btn-sm flex items-center gap-2"
          title="Alta de programa — conectar a POST /api/commercial/rebates/"
        >
          <Plus size={14} /> Nuevo programa
        </button>
      </div>

      {/* Sub-tabs */}
      <div className="flex gap-1 border-b border-border">
        {(['programs', 'ledger'] as const).map((v) => (
          <button
            key={v}
            onClick={() => setView(v)}
            className={`px-4 py-2 text-xs font-semibold border-b-2 transition-all ${
              view === v
                ? 'border-brand text-brand'
                : 'border-transparent text-text-tertiary hover:text-text-secondary'
            }`}
          >
            {v === 'programs' ? 'Programas' : 'Ledger / Accruals'}
          </button>
        ))}
      </div>

      {/* Content */}
      {view === 'programs' && <ProgramsList />}
      {view === 'ledger' && <LedgerList />}

      {/* Nota DEC-S23-01 */}
      <div className="flex items-start gap-2 p-3 rounded-lg border border-amber-200 bg-amber-50 text-xs text-amber-800">
        <AlertCircle size={14} className="mt-0.5 shrink-0" />
        <p>
          <span className="font-semibold">DEC-S23-01 pendiente:</span> El campo{' '}
          <code className="font-mono bg-amber-100 px-1 rounded">calculation_base</code>{' '}
          está en NULL hasta resolución del CEO. Los cálculos lanzarán error si se activan.
        </p>
      </div>
    </div>
  );
}
