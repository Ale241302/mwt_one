"use client";

/**
 * S23-13 — ArtifactPolicySection
 *
 * Acceso: CEO + AGENT (IsCEOOrInternalAgent)
 * Funciones:
 *  - Ver política activa como JSON formateado
 *  - Historial de versiones (tabla)
 *  - PATCH notes/is_active sobre versión activa
 *  - Botón "Seed desde constante" → llama al management command via endpoint
 */

import { useState, useEffect, useCallback } from "react";
import { RefreshCw, ChevronDown, ChevronUp, CheckCircle, History } from "lucide-react";
import api from "@/lib/api";

interface PolicyVersion {
  id: string;
  brand: string;
  version: number;
  artifact_policy: Record<string, unknown>;
  is_active: boolean;
  superseded_by: string | null;
  notes: string;
  created_at: string;
}

export function ArtifactPolicySection({ brandId }: { brandId?: string }) {
  const [versions, setVersions]       = useState<PolicyVersion[]>([]);
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState<string | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [editingNotes, setEditingNotes] = useState("");
  const [savingNotes, setSavingNotes] = useState(false);
  const [seeding, setSeeding]         = useState(false);
  const [seedMsg, setSeedMsg]         = useState<string | null>(null);

  const fetchVersions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get("/commercial/artifact-policies/");
      const all: PolicyVersion[] = res.data?.results ?? res.data ?? [];
      setVersions(brandId ? all.filter(v => v.brand === brandId) : all);
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "Error cargando políticas.");
    } finally {
      setLoading(false);
    }
  }, [brandId]);

  useEffect(() => { fetchVersions(); }, [fetchVersions]);

  const activeVersion = versions.find(v => v.is_active);
  const history = versions.filter(v => !v.is_active).sort((a, b) => b.version - a.version);

  const handleSaveNotes = async () => {
    if (!activeVersion) return;
    setSavingNotes(true);
    try {
      await api.patch(`/commercial/artifact-policies/${activeVersion.id}/`, { notes: editingNotes });
      fetchVersions();
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "Error guardando notas.");
    } finally {
      setSavingNotes(false);
    }
  };

  const handleSeed = async () => {
    if (!confirm("¿Hacer seed de ArtifactPolicy desde la constante Python? Solo aplica a marcas sin policy activa.")) return;
    setSeeding(true);
    setSeedMsg(null);
    try {
      // El endpoint llama al management command seed_artifact_policy
      const res = await api.post("/commercial/artifact-policies/seed/");
      setSeedMsg(res.data?.message ?? "Seed ejecutado correctamente.");
      fetchVersions();
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "Error ejecutando seed.");
    } finally {
      setSeeding(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-navy">Artifact Policy</h3>
          <p className="text-xs text-text-tertiary mt-0.5">Versiones versionadas — nunca se edita in-place.</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={fetchVersions} className="btn btn-sm btn-ghost p-2" title="Refrescar">
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          </button>
          <button
            onClick={handleSeed}
            disabled={seeding}
            className="btn btn-sm btn-ghost border border-border text-xs"
          >
            {seeding ? "Seeding..." : "Seed desde constante"}
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 text-red-700 text-xs px-4 py-3">{error}</div>
      )}
      {seedMsg && (
        <div className="rounded-lg bg-green-50 border border-green-200 text-green-700 text-xs px-4 py-3">{seedMsg}</div>
      )}

      {/* Active Version Viewer */}
      {loading ? (
        <div className="card p-8 text-center text-xs text-text-tertiary">Cargando...</div>
      ) : !activeVersion ? (
        <div className="card p-8 text-center text-text-tertiary">
          <CheckCircle size={36} className="mx-auto mb-3 opacity-20" />
          <p className="text-sm">No hay versión activa para esta marca.</p>
          <p className="text-xs text-text-tertiary mt-1">Usa el botón "Seed desde constante" para inicializarla.</p>
        </div>
      ) : (
        <div className="card border border-border/60 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 bg-bg-alt/30 border-b border-border">
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-green-50 text-green-700">
                <CheckCircle size={11} /> Activa
              </span>
              <span className="text-xs font-bold text-navy">v{activeVersion.version}</span>
              <span className="text-[10px] text-text-tertiary">
                {new Date(activeVersion.created_at).toLocaleDateString()}
              </span>
            </div>
          </div>

          {/* JSON Viewer */}
          <div className="bg-gray-950 text-green-300 font-mono text-[11px] p-4 max-h-72 overflow-auto leading-5">
            <pre>{JSON.stringify(activeVersion.artifact_policy, null, 2)}</pre>
          </div>

          {/* Notes Editor */}
          <div className="px-4 py-3 border-t border-border space-y-2">
            <label className="text-[10px] font-semibold text-text-tertiary uppercase">Notas (PATCH)</label>
            <div className="flex gap-2">
              <input
                className="input text-xs flex-1"
                placeholder="Añadir nota sobre esta versión..."
                defaultValue={activeVersion.notes}
                onChange={e => setEditingNotes(e.target.value)}
              />
              <button
                onClick={handleSaveNotes}
                disabled={savingNotes}
                className="btn btn-sm btn-primary"
              >
                {savingNotes ? "Guardando..." : "Guardar"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Version History */}
      {history.length > 0 && (
        <div>
          <button
            className="flex items-center gap-2 text-xs font-semibold text-text-secondary hover:text-navy transition-colors"
            onClick={() => setShowHistory(v => !v)}
          >
            <History size={14} />
            Historial de versiones ({history.length})
            {showHistory ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
          </button>

          {showHistory && (
            <div className="card mt-3 shadow-sm overflow-hidden border-border/60">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="bg-bg-alt/30 border-b border-border">
                    {["Versión","Creada","Notas","Superada por"].map(h => (
                      <th key={h} className="px-4 py-3 font-semibold text-text-tertiary text-[10px] uppercase">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/50">
                  {history.map(v => (
                    <tr key={v.id} className="hover:bg-brand/[0.02] transition-colors">
                      <td className="px-4 py-3 font-bold text-navy">v{v.version}</td>
                      <td className="px-4 py-3 text-text-tertiary">{new Date(v.created_at).toLocaleDateString()}</td>
                      <td className="px-4 py-3 text-text-secondary">{v.notes || <span className="italic text-text-tertiary">—</span>}</td>
                      <td className="px-4 py-3 font-mono text-[10px] text-text-tertiary">
                        {v.superseded_by ? v.superseded_by.substring(0, 8) + "…" : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
