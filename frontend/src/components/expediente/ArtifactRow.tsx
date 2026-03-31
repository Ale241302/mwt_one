"use client";
import React from "react";
import { CheckCircle, Clock, XCircle, AlertCircle, Play, Lock, PlusCircle } from "lucide-react";

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
  isAvailable: boolean;
  onExecute: (cmd: string, artifact?: any) => void;
  blockReason?: string;
  isAdmin?: boolean;
}

export default function ArtifactRow({
  commandKey,
  label,
  artifact,
  allArtifacts,
  isAvailable,
  onExecute,
  blockReason,
  isAdmin,
}: ArtifactRowProps) {
  const isCompleted = artifact?.status === "completed" || artifact?.status === "COMPLETED";
  const isVoided = artifact?.status === "voided" || artifact?.status === "VOIDED";

  // Historial completo de este tipo de artefacto (para mostrar debajo)
  const history = allArtifacts ?? (artifact ? [artifact] : []);

  return (
    <div className="flex flex-col">
      <div className="flex items-center justify-between px-5 py-3 gap-4 hover:bg-bg transition-colors">
        <div className="flex items-center gap-3 min-w-0">
          <span className="font-mono text-[11px] text-text-tertiary w-8 shrink-0">{commandKey}</span>

          {isCompleted ? (
            <CheckCircle size={14} className="text-success" />
          ) : isVoided ? (
            <XCircle size={14} className="text-coral" />
          ) : artifact?.status === "superseded" ? (
            <AlertCircle size={14} className="text-text-tertiary" />
          ) : (
            <Clock size={14} className="text-warning" />
          )}

          <div className="min-w-0">
            <p className="text-sm font-medium text-navy truncate flex items-center gap-2">
              {label}
              {isCompleted && (
                <span className="badge badge-success px-1.5 py-0.5 text-[10px]">COMPLETADO ✓</span>
              )}
              {isVoided && (
                <span className="badge badge-critical px-1.5 py-0.5 text-[10px]">Anulado ❌</span>
              )}
              {blockReason && (
                <span
                  className="badge px-1.5 py-0.5 text-[10px] bg-slate-100 text-slate-500 flex items-center gap-1"
                  title={blockReason}
                >
                  <Lock size={10} /> BLOQUEADO
                </span>
              )}
            </p>
            {artifact && (
              <p className="caption text-text-tertiary">
                {new Date(artifact.created_at).toLocaleDateString("es-CO")}
              </p>
            )}
          </div>
        </div>

        <div className="shrink-0 flex items-center gap-2">
          {/* Siempre mostrar "Ver detalle" si hay un artefacto registrado */}
          {artifact && (
            <button
              className="btn btn-sm btn-ghost border border-[var(--border)] text-[var(--text-secondary)]"
              onClick={() => onExecute(commandKey, artifact)}
            >
              Ver detalle
            </button>
          )}

          {/* Mostrar "Nuevo registro" cuando ya existe uno Y la acción está disponible */}
          {isCompleted && isAvailable && (
            <button
              className="btn btn-sm btn-primary flex items-center gap-1"
              onClick={() => onExecute(commandKey, undefined)}
              aria-label={`Nuevo registro ${commandKey}`}
            >
              <PlusCircle size={12} /> Nuevo registro
            </button>
          )}

          {/* Mostrar "Registrar" cuando NO hay artefacto aún */}
          {!artifact && !isVoided && isAvailable && (
            <button
              className="btn btn-sm btn-primary"
              onClick={() => onExecute(commandKey, undefined)}
              aria-label={`Ejecutar ${commandKey}`}
            >
              <Play size={12} /> Registrar
            </button>
          )}

          {/* Registrar deshabilitado si no hay acción disponible y tampoco artefacto */}
          {!artifact && !isVoided && !isAvailable && (
            <button
              className="btn btn-sm btn-ghost opacity-50 cursor-not-allowed"
              disabled
            >
              <Play size={12} /> Registrar
            </button>
          )}
        </div>
      </div>

      {/* Historial de registros anteriores (más de uno del mismo tipo) */}
      {history.length > 1 && (
        <div className="mx-5 mb-3 border border-divider rounded-lg overflow-hidden">
          <p className="text-[10px] font-semibold text-text-tertiary uppercase tracking-wider px-3 py-1.5 bg-bg border-b border-divider">
            Historial de registros ({history.length})
          </p>
          {history.map((h, i) => (
            <div
              key={i}
              className="flex items-center justify-between px-3 py-2 text-sm border-b border-divider last:border-b-0 hover:bg-bg transition-colors"
            >
              <div className="flex items-center gap-2">
                <span className="text-text-tertiary text-[11px]">{i + 1}.</span>
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
                  {new Date(h.created_at).toLocaleDateString("es-CO")}
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
    </div>
  );
}
