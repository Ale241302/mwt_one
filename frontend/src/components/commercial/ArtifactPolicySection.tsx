// S23-13 — ArtifactPolicySection: viewer + historial de versiones + seed desde constante
"use client";

import React, { useState } from 'react';
import {
  FileCode, RefreshCw, Clock, CheckCircle, AlertCircle, ChevronDown, ChevronUp
} from 'lucide-react';

// ─── Tipos ────────────────────────────────────────────────────────────────────
interface PolicyVersion {
  id: string;
  version: number;
  is_active: boolean;
  created_at: string;
  created_by: string;
  artifact_policy: Record<string, unknown>;
  superseded_by: string | null;
}

// ─── Mock data — reemplazar con fetch a /api/commercial/artifact-policy/ ──────
const MOCK_VERSIONS: PolicyVersion[] = [
  {
    id: 'apv-2',
    version: 2,
    is_active: true,
    created_at: '2026-03-15T10:30:00Z',
    created_by: 'CEO',
    artifact_policy: {
      proforma: { requires_approval: true, approval_roles: ['CEO', 'AGENT_SR'] },
      invoice:  { requires_approval: false, auto_generate: true },
      packing:  { requires_approval: false, auto_generate: true },
      label:    { requires_approval: true, approval_roles: ['CEO'] },
    },
    superseded_by: null,
  },
  {
    id: 'apv-1',
    version: 1,
    is_active: false,
    created_at: '2026-01-01T08:00:00Z',
    created_by: 'seed_artifact_policy',
    artifact_policy: {
      proforma: { requires_approval: true, approval_roles: ['CEO'] },
      invoice:  { requires_approval: false, auto_generate: true },
    },
    superseded_by: 'apv-2',
  },
];

function JsonViewer({ data }: { data: Record<string, unknown> }) {
  return (
    <pre className="text-[11px] font-mono bg-bg-alt rounded-lg p-4 overflow-auto max-h-64 text-text-secondary leading-relaxed">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}

export function ArtifactPolicySection() {
  const [versions] = useState<PolicyVersion[]>(MOCK_VERSIONS);
  const [expandedId, setExpandedId] = useState<string | null>(MOCK_VERSIONS[0]?.id ?? null);
  const [seeding, setSeeding] = useState(false);
  const [seedMsg, setSeedMsg] = useState<string | null>(null);

  const activeVersion = versions.find((v) => v.is_active);

  const handleSeed = async () => {
    setSeeding(true);
    setSeedMsg(null);
    try {
      // TODO: POST /api/commercial/artifact-policy/seed/
      await new Promise((r) => setTimeout(r, 900)); // simular latencia
      setSeedMsg('Seed ejecutado correctamente. Brands sin policy activa han recibido versión inicial.');
    } catch {
      setSeedMsg('Error al ejecutar seed. Revisa los logs.');
    } finally {
      setSeeding(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="heading-lg">ArtifactPolicy</h2>
          <p className="text-xs text-text-tertiary mt-0.5">
            Política de artefactos versionada append-only. Cada PATCH crea nueva versión; no se edita in-place.
          </p>
        </div>
        <button
          onClick={handleSeed}
          disabled={seeding}
          className="btn btn-secondary btn-sm flex items-center gap-2 disabled:opacity-60"
          title="Ejecutar management command seed_artifact_policy"
        >
          <RefreshCw size={13} className={seeding ? 'animate-spin' : ''} />
          {seeding ? 'Ejecutando...' : 'Seed desde constante'}
        </button>
      </div>

      {/* Mensaje seed */}
      {seedMsg && (
        <div className={`flex items-start gap-2 p-3 rounded-lg border text-xs ${
          seedMsg.includes('Error')
            ? 'border-red-200 bg-red-50 text-red-800'
            : 'border-emerald-200 bg-emerald-50 text-emerald-800'
        }`}>
          {seedMsg.includes('Error')
            ? <AlertCircle size={14} className="mt-0.5 shrink-0" />
            : <CheckCircle size={14} className="mt-0.5 shrink-0" />}
          <p>{seedMsg}</p>
        </div>
      )}

      {/* Versión activa destacada */}
      {activeVersion && (
        <div className="card border-2 border-brand/30 overflow-hidden">
          <div className="flex items-center justify-between px-5 py-3 bg-brand/[0.03]">
            <div className="flex items-center gap-2">
              <CheckCircle size={14} className="text-brand" />
              <span className="text-xs font-bold text-brand">Versión activa — v{activeVersion.version}</span>
            </div>
            <span className="text-[10px] text-text-tertiary font-mono">
              {new Date(activeVersion.created_at).toLocaleDateString('es-CO')} · {activeVersion.created_by}
            </span>
          </div>
          <div className="px-5 py-4">
            <JsonViewer data={activeVersion.artifact_policy} />
          </div>
        </div>
      )}

      {/* Historial de versiones */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <Clock size={14} className="text-text-tertiary" />
          <p className="text-xs font-semibold text-text-secondary">Historial de versiones</p>
        </div>
        <div className="space-y-2">
          {versions.map((ver) => (
            <div key={ver.id} className="card overflow-hidden">
              <div className="flex items-center justify-between px-5 py-3">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${ver.is_active ? 'bg-brand' : 'bg-text-tertiary'}`} />
                  <div>
                    <span className="text-xs font-semibold text-text-primary">v{ver.version}</span>
                    <span className="ml-2 text-[10px] text-text-tertiary">
                      {new Date(ver.created_at).toLocaleDateString('es-CO')} · {ver.created_by}
                    </span>
                    {ver.is_active && (
                      <span className="ml-2 inline-flex items-center px-1.5 py-0.5 rounded border border-brand/30 bg-brand/10 text-brand text-[10px] font-semibold">
                        ACTIVA
                      </span>
                    )}
                    {ver.superseded_by && (
                      <span className="ml-2 text-[10px] text-text-tertiary">
                        → superada
                      </span>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => setExpandedId(expandedId === ver.id ? null : ver.id)}
                  className="btn btn-ghost btn-sm p-2"
                >
                  {expandedId === ver.id ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                </button>
              </div>

              {expandedId === ver.id && (
                <div className="border-t border-border px-5 py-4">
                  <JsonViewer data={ver.artifact_policy} />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Nota append-only */}
      <div className="flex items-start gap-2 p-3 rounded-lg border border-sky-200 bg-sky-50 text-xs text-sky-800">
        <FileCode size={14} className="mt-0.5 shrink-0" />
        <p>
          <span className="font-semibold">Append-only:</span> Nunca se edita una versión existente.
          Cada cambio crea una nueva versión y desactiva la anterior dentro de{' '}
          <code className="font-mono bg-sky-100 px-1 rounded">transaction.atomic()</code>.
        </p>
      </div>
    </div>
  );
}
