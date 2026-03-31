"use client";
/**
 * S10-03 / S20B — Detalle expediente con acordeón de artefactos y estados canónicos.
 * Corregido: modal conectado correctamente, "Ver detalle" y "Nuevo registro" funcionan,
 * "Agregar Opcional" abre el modal, historial de eventos visible.
 */
import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import ArtifactModal from "./ArtifactModal";
import ArtifactRow from "./ArtifactRow";
import ArtifactSection from "./ArtifactSection";
import { CANONICAL_STATES } from "@/constants/states";
import { isLegacyExpediente } from "@/utils/legacy-check";
import {
  LEGACY_STATE_ARTIFACTS,
  LEGACY_ARTIFACT_COMMAND_MAP,
  LEGACY_ARTIFACT_LABELS,
} from "@/app/[lang]/(mwt)/(dashboard)/expedientes/[id]/legacy-artifacts";

interface Artifact {
  artifact_type: string;
  status: string;
  created_at: string;
  payload?: any;
}

interface ExpedienteAccordionProps {
  expedienteId: string;
  expedienteData: any;
  artifacts: Artifact[];
  availableActions:
    | { primary: any[]; secondary: any[]; ops: any[] }
    | string[];
  onRefresh: () => void;
  currentState: string;
  onActionClick?: (commandKey: string, artifact?: any) => void;
  /** Si el usuario autenticado es admin/staff — habilita acciones extras */
  isAdmin?: boolean;
}

export default function ExpedienteAccordion({
  expedienteId,
  expedienteData,
  artifacts,
  availableActions,
  onRefresh,
  currentState,
  onActionClick,
  isAdmin,
}: ExpedienteAccordionProps) {
  // ── Helpers de acciones disponibles ──────────────────────────────────────
  const hasAction = (actionId: string) => {
    if (!availableActions) return false;
    if (Array.isArray(availableActions)) return availableActions.includes(actionId);
    const { primary, secondary, ops } = availableActions as any;
    return (
      (Array.isArray(primary) && primary.some((a: any) => a.id === actionId)) ||
      (Array.isArray(secondary) && secondary.some((a: any) => a.id === actionId)) ||
      (Array.isArray(ops) && ops.some((a: any) => a.id === actionId))
    );
  };

  // ── Estado local del acordeón ─────────────────────────────────────────────
  const [openPhases, setOpenPhases] = useState<Record<string, boolean>>({[currentState]: true});
  const toggle = (label: string) =>
    setOpenPhases((prev) => ({ ...prev, [label]: !prev[label] }));

  // ── Modal interno (para cuando no se pasa onActionClick externo) ──────────
  // activeModal = { commandKey, artifact? }
  // artifact = undefined → modo creación
  // artifact = objeto   → modo "Ver detalle" (readOnly)
  const [activeModal, setActiveModal] = useState<{ commandKey: string; artifact?: any } | null>(null);

  /**
   * Manejador unificado: se llama desde ArtifactSection / ArtifactRow.
   * - artifact = undefined → abrir en modo creación (Registrar / Nuevo registro)
   * - artifact = objeto   → abrir en modo solo lectura (Ver detalle)
   */
  const handleExecute = (commandKey: string, artifact?: any) => {
    if (onActionClick) {
      // Propagar al padre si está definido (ej. para que el padre maneje el refetch)
      onActionClick(commandKey, artifact);
    } else {
      setActiveModal({ commandKey, artifact });
    }
  };

  const isLegacy = isLegacyExpediente(expedienteData);
  const currentIdx = CANONICAL_STATES.indexOf(currentState as any);

  const statesToRender = isLegacy
    ? CANONICAL_STATES
    : CANONICAL_STATES.filter((_, idx) => idx <= currentIdx);

  return (
    <div className="space-y-3">
      {statesToRender.map((stateName) => {
        const stateIdx = CANONICAL_STATES.indexOf(stateName as any);

        if (!isLegacy && stateIdx > currentIdx) return null;

        const isOpen = !!openPhases[stateName];

        // ── MODO LEGACY ────────────────────────────────────────────────────
        if (isLegacy) {
          const stateArtifactTypes = Array.isArray(LEGACY_STATE_ARTIFACTS[stateName])
            ? LEGACY_STATE_ARTIFACTS[stateName]
            : [];
          if (stateName === "CERRADO" && stateArtifactTypes.length === 0) return null;

          const phaseArtifacts = (Array.isArray(artifacts) ? artifacts : []).filter((a) =>
            stateArtifactTypes.includes(a.artifact_type)
          );
          const completedCount = phaseArtifacts.filter((a) => a.status === "completed").length;
          const commandsInState = stateArtifactTypes
            .map((type) => LEGACY_ARTIFACT_COMMAND_MAP[type])
            .filter(Boolean);
          const hasAvailable = commandsInState.some((cmd) => hasAction(cmd));

          return (
            <div key={stateName} className="card overflow-hidden">
              <button
                className="w-full flex items-center justify-between px-5 py-3 hover:bg-bg transition-colors"
                onClick={() => toggle(stateName)}
                aria-expanded={isOpen}
              >
                <div className="flex items-center gap-3">
                  <span className="heading-sm font-semibold text-navy">{stateName}</span>
                  <span className="caption text-text-tertiary">
                    {completedCount} / {stateArtifactTypes.length} completados
                  </span>
                  {hasAvailable && (
                    <span className="badge badge-info text-[10px]">Acción disponible</span>
                  )}
                </div>
                {isOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
              </button>

              {isOpen && stateArtifactTypes.length > 0 && (
                <div className="border-t border-divider divide-y divide-divider">
                  {stateArtifactTypes.map((artType) => {
                    const cmdKey = LEGACY_ARTIFACT_COMMAND_MAP[artType];
                    if (!cmdKey) return null;

                    const allOfType = (Array.isArray(artifacts) ? artifacts : [])
                      .filter((a) => a.artifact_type === artType)
                      .sort(
                        (a, b) =>
                          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
                      );
                    const latestArt = allOfType[0];
                    const isAvailable = hasAction(cmdKey);

                    return (
                      <ArtifactRow
                        key={artType}
                        artifactType={artType}
                        commandKey={cmdKey}
                        label={LEGACY_ARTIFACT_LABELS[artType] ?? artType}
                        artifact={latestArt as any}
                        allArtifacts={allOfType as any}
                        isAvailable={isAvailable}
                        onExecute={handleExecute}
                        isAdmin={isAdmin}
                      />
                    );
                  })}
                </div>
              )}
            </div>
          );
        }

        // ── MODO MODERNO (policy-driven) ────────────────────────────────────
        const policyForState = expedienteData?.artifact_policy?.[stateName];
        if (!policyForState) return null;

        const stateArtifactTypes = [
          ...policyForState.required,
          ...policyForState.optional,
        ];

        if (stateArtifactTypes.length === 0 && stateName === "CERRADO") return null;

        const phaseArtifacts = (Array.isArray(artifacts) ? artifacts : []).filter((a) =>
          stateArtifactTypes.includes(a.artifact_type)
        );
        const completedCount = phaseArtifacts.filter(
          (a) => a.status && a.status.toUpperCase() === "COMPLETED"
        ).length;

        return (
          <div key={stateName} className="card overflow-hidden">
            <button
              className="w-full flex items-center justify-between px-5 py-3 hover:bg-bg transition-colors"
              onClick={() => toggle(stateName)}
              aria-expanded={isOpen}
            >
              <div className="flex items-center gap-3">
                <span className="heading-sm font-semibold text-navy">
                  {stateName}{" "}
                  {stateIdx < currentIdx && (
                    <span className="text-success ml-2">✓</span>
                  )}
                </span>
                <span className="caption text-text-tertiary">
                  {completedCount} completados
                </span>
              </div>
              {isOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            </button>

            {isOpen && (
              <div className="border-t border-divider">
                <ArtifactSection
                  policyState={policyForState}
                  artifacts={artifacts}
                  availableActions={availableActions as any}
                  onExecute={handleExecute}
                  hasAction={hasAction}
                  isAdmin={isAdmin}
                />
              </div>
            )}
          </div>
        );
      })}

      {/* ── Modal unificado ──────────────────────────────────────────────── */}
      {activeModal && (
        <ArtifactModal
          open={true}
          expedienteId={expedienteId}
          commandKey={activeModal.commandKey}
          artifact={activeModal.artifact}
          // Si artifact está definido → readOnly (Ver detalle)
          // Si artifact es undefined  → modo creación (Registrar / Nuevo registro)
          readOnly={activeModal.artifact !== undefined}
          onClose={() => setActiveModal(null)}
          onSuccess={() => {
            setActiveModal(null);
            onRefresh();
          }}
        />
      )}
    </div>
  );
}
