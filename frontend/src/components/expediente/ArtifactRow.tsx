"use client";
import React from "react";
import { CheckCircle, Clock, XCircle, AlertCircle, Play, Lock } from "lucide-react";

interface ArtifactRowProps {
  artifactType: string;
  commandKey: string;
  label: string;
  artifact?: {
    status: string;
    created_at: string;
  };
  isAvailable: boolean;
  onExecute: (cmd: string) => void;
  blockReason?: string;
}

export default function ArtifactRow({
  commandKey,
  label,
  artifact,
  isAvailable,
  onExecute,
  blockReason,
}: ArtifactRowProps) {
  const isCompleted = artifact?.status === "completed";
  const isPending = !artifact;

  return (
    <div className="flex items-center justify-between px-5 py-3 gap-4 hover:bg-bg transition-colors">
      <div className="flex items-center gap-3 min-w-0">
        <span className="font-mono text-[11px] text-text-tertiary w-8 shrink-0">{commandKey}</span>
        
        {isCompleted ? (
          <CheckCircle size={14} className="text-success" />
        ) : artifact?.status === "voided" ? (
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
              <span className="badge badge-success px-1.5 py-0.5 text-[10px]">COMPLETADO</span>
            )}
            {blockReason && (
              <span className="badge px-1.5 py-0.5 text-[10px] bg-slate-100 text-slate-500 flex items-center gap-1" title={blockReason}>
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
        {isAvailable ? (
          <button
            className="btn btn-sm btn-primary"
            onClick={() => onExecute(commandKey)}
            aria-label={`Ejecutar ${commandKey}`}
          >
            <Play size={12} /> Registrar
          </button>
        ) : (
          <button
            className="btn btn-sm btn-ghost opacity-50 cursor-not-allowed"
            disabled
          >
            <Play size={12} /> Registrar
          </button>
        )}
      </div>
    </div>
  );
}
