"use client";
import React from "react";
import {
  CheckCircle, Clock, XCircle, AlertCircle,
  Play, Lock, PlusCircle, Trash2, History,
} from "lucide-react";

interface ArtifactRowProps {
  artifactType: string;
  commandKey: string;
  label: string;
  artifact?: {
    status: string;
    created_at: string;
    payload?: any;
  };
  allArtifacts?: Array<{ status: string; created_at: string; payload?: any; artifact_type: string }>;
  /** Total de registros de este tipo en el expediente */
  recordCount?: number;
  isAvailable: boolean;
  onExecute: (cmd: string, artifact?: any) => void;
  blockReason?: string;
  isAdmin?: boolean;
  /** Solo admin: callback para quitar este tipo de artefacto de la policy */
  onRemoveArtifactType?: (artifactType: string) => void;
}

export default function ArtifactRow({
  artifactType,
  commandKey,
  label,
  artifact,
  allArtifacts,
  recordCount = 0,
  isAvailable,
  onExecute,
  blockReason,
  isAdmin,
  onRemoveArtifactType,
}: ArtifactRowProps) {
  const [historyOpen, setHistoryOpen] = React.useState(false);

  const isCompleted = artifact?.status === "completed" || artifact?.status === "COMPLETED";
  const isVoided    = artifact?.status === "voided"    || artifact?.status === "VOIDED";

  // Historial completo ordenado por fecha desc
  const history = allArtifacts && allArtifacts.length > 0
    ? allArtifacts
    : artifact
    ? [artifact]
    : [];

  // Admin puede crear nuevo registro aunque el backend no lo marque como disponible
  const canCreateNew = isCompleted && (isAvailable || isAdmin);

  const effectiveCount = recordCount > 0 ? recordCount : history.length;

  return (
    <div className="flex flex-col">
      <div className="flex items-center justify-between px-5 py-3 gap-4 hover:bg-bg transition-colors">

        {/* ── Left: icon + label + badges ── */}
        <div className="flex items-center gap-3 min-w-0">
          {/* Status icon */}
          <span className="shrink-0">
            {isCompleted ? (
              <CheckCircle size={14} className="text-success" />
            ) : isVoided ? (
              <XCircle size={14} className="text-coral" />
            ) : artifact?.status === "superseded" ? (
              <AlertCircle size={14} className="text-text-tertiary" />
            ) : (
              <Clock size={14} className="text-warning" />
            )}
          </span>

          <div className="min-w-0">
            <p className="text-sm font-medium text-navy truncate flex items-center gap-2 flex-wrap">
              {label}

              {/* Completed badge */}
              {isCompleted && (
                <span className="badge badge-success px-1.5 py-0.5 text-[10px] shrink-0">
                  ✓ COMPLETADO
                </span>
              )}

              {/* Voided badge */}
              {isVoided && (
                <span className="badge badge-critical px-1.5 py-0.5 text-[10px] shrink-0">
                  ❌ Anulado
                </span>
              )}

              {/* Gate / blocked badge */}
              {blockReason && (
                <span
                  className="badge px-1.5 py-0.5 text-[10px] bg-slate-100 text-slate-500 flex items-center gap-1 shrink-0"
                  title={blockReason}
                >
                  <Lock size={10} /> BLOQUEADO
                </span>
              )}

              {/* Record count badge — shown when there are records */}
              {effectiveCount > 0 && (
                <button
                  onClick={() => setHistoryOpen((p) => !p)}
                  className="inline-flex items-center gap-1 badge bg-slate-100 text-slate-600 hover:bg-slate-200 transition-colors px-1.5 py-0.5 text-[10px] shrink-0 cursor-pointer"
                  title="Ver historial de registros"
                >
                  <History size={9} />
                  {effectiveCount} {effectiveCount === 1 ? "registro" : "registros"}
                </button>
              )}
            </p>

            {/* Latest timestamp */}
            {artifact && (
              <p className="caption text-text-tertiary">
                Último:{" "}
                {new Date(artifact.created_at).toLocaleDateString("es-CO", {
                  day: "2-digit",
                  month: "short",
                  year: "numeric",
                })}
              </p>
            )}
          </div>
        </div>

        {/* ── Right: action buttons ── */}
        <div className="shrink-0 flex items-center gap-2">

          {/* Ver detalle del registro más reciente */}
          {artifact && (
            <button
              className="btn btn-sm btn-ghost border border-[var(--border)] text-[var(--text-secondary)]"
              onClick={() => onExecute(commandKey, artifact)}
            >
              Ver detalle
            </button>
          )}

          {/* Nuevo registro: disponible cuando está completado y (hay acción ó es admin) */}
          {canCreateNew && (
            <button
              className="btn btn-sm btn-primary flex items-center gap-1"
              onClick={() => onExecute(commandKey, undefined)}
              aria-label={`Nuevo registro ${commandKey}`}
            >
              <PlusCircle size={12} /> Nuevo registro
            </button>
          )}

          {/* Registrar por primera vez */}
          {!artifact && !isVoided && isAvailable && (
            <button
              className="btn btn-sm btn-primary flex items-center gap-1"
              onClick={() => onExecute(commandKey, undefined)}
              aria-label={`Ejecutar ${commandKey}`}
            >
              <Play size={12} /> Registrar
            </button>
          )}

          {/* Admin puede registrar aunque no esté disponible en el backend */}
          {!artifact && !isVoided && !isAvailable && isAdmin && (
            <button
              className="btn btn-sm btn-ghost border border-dashed border-amber-400 text-amber-600 flex items-center gap-1"
              onClick={() => onExecute(commandKey, undefined)}
              title="Admin: forzar registro"
            >
              <Play size={12} /> Registrar (admin)
            </button>
          )}

          {/* Sin acción disponible ni admin */}
          {!artifact && !isVoided && !isAvailable && !isAdmin && (
            <button
              className="btn btn-sm btn-ghost opacity-50 cursor-not-allowed"
              disabled
            >
              <Play size={12} /> Registrar
            </button>
          )}

          {/* Admin: quitar tipo de artefacto de la policy */}
          {isAdmin && onRemoveArtifactType && (
            <button
              className="btn btn-sm btn-ghost text-red-400 hover:text-red-600 hover:bg-red-50"
              onClick={() => onRemoveArtifactType(artifactType)}
              title="Admin: quitar artefacto de esta fase"
            >
              <Trash2 size={12} />
            </button>
          )}
        </div>
      </div>

      {/* ── Historial de registros (expandible) ── */}
      {historyOpen && history.length > 0 && (
        <div className="mx-5 mb-3 border border-divider rounded-lg overflow-hidden">
          <div className="flex items-center justify-between px-3 py-1.5 bg-bg border-b border-divider">
            <p className="text-[10px] font-semibold text-text-tertiary uppercase tracking-wider">
              Historial de registros — {history.length} {history.length === 1 ? "entrada" : "entradas"}
            </p>
            <button
              className="text-[10px] text-text-tertiary hover:text-text transition-colors"
              onClick={() => setHistoryOpen(false)}
            >
              Cerrar ✕
            </button>
          </div>

          {history.map((h, i) => (
            <div
              key={i}
              className="flex items-center justify-between px-3 py-2 text-sm border-b border-divider last:border-b-0 hover:bg-bg transition-colors"
            >
              <div className="flex items-center gap-2">
                <span className="text-text-tertiary text-[11px] w-5">{i + 1}.</span>
                <span
                  className={`badge text-[10px] px-1.5 py-0.5 ${
                    h.status === "COMPLETED" || h.status === "completed"
                      ? "badge-success"
                      : h.status === "VOIDED" || h.status === "voided"
                      ? "badge-critical"
                      : "badge-info"
                  }`}
                >
                  {h.status}
                </span>
                <span className="text-text-tertiary text-[11px]">
                  {new Date(h.created_at).toLocaleDateString("es-CO", {
                    day: "2-digit",
                    month: "short",
                    year: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </span>
              </div>
              <button
                className="btn btn-sm btn-ghost border border-[var(--border)] text-[var(--text-secondary)] text-[11px]"
                onClick={() => onExecute(commandKey, h)}
              >
                Ver
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Mostrar historial automáticamente si hay > 1 y historyOpen no está controlado */}
      {!historyOpen && history.length > 1 && (
        <div className="mx-5 mb-2">
          <button
            onClick={() => setHistoryOpen(true)}
            className="text-[11px] text-text-tertiary hover:text-primary flex items-center gap-1 transition-colors"
          >
            <History size={10} />
            Ver {history.length} registros anteriores
          </button>
        </div>
      )}
    </div>
  );
}
