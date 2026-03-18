"use client";
/**
 * S10-03 — Detalle expediente con acordeón de artefactos.
 * Renders all artifact phases as collapsible sections.
 */
import { useState } from "react";
import { ChevronDown, ChevronRight, CheckCircle, Clock, XCircle, AlertCircle, Play } from "lucide-react";
import { cn } from "@/lib/utils";
import ArtifactModal from "./ArtifactModal";

interface Artifact {
  artifact_id: string;
  artifact_type: string;
  status: "pending" | "completed" | "voided" | "superseded";
  created_at: string;
  payload: Record<string, unknown>;
}

interface Phase {
  label: string;
  commands: string[];
  artifacts: Artifact[];
}

interface ExpedienteAccordionProps {
  expedienteId: string;
  artifacts: Artifact[];
  availableActions: string[];
  onRefresh: () => void;
}

const PHASES: { label: string; commands: string[] }[] = [
  { label: "Inicio",         commands: ["C2", "C3", "C4", "C5", "C6"] },
  { label: "Logística",      commands: ["C7", "C8", "C9", "C10", "C11", "C12"] },
  { label: "Finanzas",       commands: ["C13", "C15", "C21", "C22"] },
  { label: "Cierre",         commands: ["C14", "C16", "C17", "C18"] },
];

const ARTIFACT_COMMAND_MAP: Record<string, string> = {
  "ART-01": "C2", "ART-02": "C3", "ART-03": "C4",
  "ART-04": "C5", "ART-05": "C6", "ART-06": "C7",
  "ART-07": "C8", "ART-08": "C9", "ART-09": "C13",
  "ART-10": "C11", "ART-12": "C21", "ART-19": "C22",
};

const ARTIFACT_LABELS: Record<string, string> = {
  "ART-01": "Orden de Compra", "ART-02": "Proforma", "ART-03": "Decisión Modal",
  "ART-04": "SAP Confirmado",  "ART-05": "Confirmación Producción", "ART-06": "Embarque",
  "ART-07": "Cotización Flete","ART-08": "Aduana", "ART-09": "Factura MWT",
  "ART-10": "Salida", "ART-12": "Pago Registrado", "ART-19": "Factura Comisión",
};

function ArtifactStatusIcon({ status }: { status: string }) {
  switch (status) {
    case "completed":  return <CheckCircle size={14} className="text-success" />;
    case "pending":    return <Clock size={14} className="text-warning" />;
    case "voided":     return <XCircle size={14} className="text-coral" />;
    case "superseded": return <AlertCircle size={14} className="text-text-tertiary" />;
    default:           return <Clock size={14} className="text-text-tertiary" />;
  }
}

export default function ExpedienteAccordion({
  expedienteId, artifacts, availableActions, onRefresh
}: ExpedienteAccordionProps) {
  const [openPhases, setOpenPhases] = useState<Record<string, boolean>>({ "Inicio": true });
  const [activeModal, setActiveModal] = useState<string | null>(null);

  const toggle = (label: string) =>
    setOpenPhases((prev) => ({ ...prev, [label]: !prev[label] }));

  const getArtifactsForCommand = (cmd: string) =>
    artifacts.filter((a) => ARTIFACT_COMMAND_MAP[a.artifact_type] === cmd);

  return (
    <div className="space-y-3">
      {PHASES.map((phase) => {
        const isOpen = !!openPhases[phase.label];
        const phaseArtifacts = artifacts.filter((a) =>
          phase.commands.includes(ARTIFACT_COMMAND_MAP[a.artifact_type] ?? "")
        );
        const completedCount = phaseArtifacts.filter((a) => a.status === "completed").length;
        const hasAvailable = phase.commands.some((cmd) => availableActions.includes(cmd));

        return (
          <div key={phase.label} className="card overflow-hidden">
            {/* Phase Header */}
            <button
              className="w-full flex items-center justify-between px-5 py-3 hover:bg-bg transition-colors"
              onClick={() => toggle(phase.label)}
              aria-expanded={isOpen}
            >
              <div className="flex items-center gap-3">
                <span className="heading-sm font-semibold text-navy">{phase.label}</span>
                <span className="caption text-text-tertiary">{completedCount}/{phase.commands.length} completados</span>
                {hasAvailable && (
                  <span className="badge badge-primary text-[10px]">Acción disponible</span>
                )}
              </div>
              {isOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            </button>

            {/* Phase Body */}
            {isOpen && (
              <div className="border-t border-divider divide-y divide-divider">
                {phase.commands.map((cmd) => {
                  const cmdArtifacts = getArtifactsForCommand(cmd);
                  const isAvailable = availableActions.includes(cmd);
                  const latest = cmdArtifacts[0];

                  return (
                    <div key={cmd} className="flex items-center justify-between px-5 py-3 gap-4">
                      <div className="flex items-center gap-3 min-w-0">
                        <span className="font-mono text-[11px] text-text-tertiary w-8 shrink-0">{cmd}</span>
                        {latest ? (
                          <ArtifactStatusIcon status={latest.status} />
                        ) : (
                          <div className="w-3.5 h-3.5 rounded-full border-2 border-border" />
                        )}
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-navy truncate">
                            {ARTIFACT_LABELS[Object.keys(ARTIFACT_COMMAND_MAP).find((k) => ARTIFACT_COMMAND_MAP[k] === cmd) ?? ""] ?? cmd}
                          </p>
                          {latest && (
                            <p className="caption text-text-tertiary">
                              {latest.status} · {new Date(latest.created_at).toLocaleDateString("es-CO")}
                            </p>
                          )}
                        </div>
                      </div>
                      {isAvailable && (
                        <button
                          className="btn btn-sm btn-primary shrink-0"
                          onClick={() => setActiveModal(cmd)}
                          aria-label={`Ejecutar ${cmd}`}
                        >
                          <Play size={12} /> Ejecutar
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}

      {/* Artifact Modal */}
      {activeModal && (
        <ArtifactModal
          open={true}
          expedienteId={expedienteId}
          commandKey={activeModal}
          onClose={() => setActiveModal(null)}
          onSuccess={onRefresh}
        />
      )}
    </div>
  );
}
