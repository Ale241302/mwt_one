"use client";
/**
 * S10-03 / S20B — Detalle expediente con acordeón de artefactos y estados canónicos.
 * S21   — Admin panel: avanzar/retroceder estado + agregar/quitar artefactos (solo is_superuser).
 */
import { useState } from "react";
import { ChevronDown, ChevronRight, ChevronRight as ArrowRight, ArrowLeft, Plus, AlertTriangle } from "lucide-react";
import ArtifactModal from "./ArtifactModal";
import ArtifactRow from "./ArtifactRow";
import ArtifactSection from "./ArtifactSection";
import AddArtifactModal from "./AddArtifactModal";
import { ARTIFACT_UI_REGISTRY } from "@/constants/artifact-ui-registry";
import { CANONICAL_STATES, TIMELINE_STEPS } from "@/constants/states";
import { isLegacyExpediente } from "@/utils/legacy-check";
import {
  LEGACY_STATE_ARTIFACTS,
  LEGACY_ARTIFACT_COMMAND_MAP,
  LEGACY_ARTIFACT_LABELS,
} from "@/app/[lang]/(mwt)/(dashboard)/expedientes/[id]/legacy-artifacts";
import api from "@/lib/api";
import toast from "react-hot-toast";

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
  /** Si el usuario autenticado es is_superuser de Django */
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

  // ── Modal interno ─────────────────────────────────────────────────────────
  const [activeModal, setActiveModal] = useState<{ commandKey: string; artifact?: any } | null>(null);

  // Admin: state to know which phase is currently adding an artifact via modal
  const [addArtifactToState, setAddArtifactToState] = useState<string | null>(null);


  const handleExecute = (commandKey: string, artifact?: any) => {
    setActiveModal({ commandKey, artifact });
  };

  const handleSuccess = () => {
    setActiveModal(null);
    onRefresh();
  };

  // ── Admin: avanzar / retroceder estado ────────────────────────────────────
  const [stateLoading, setStateLoading] = useState<"advance" | "revert" | null>(null);

  const advanceState = async () => {
    if (!window.confirm("¿Confirmas avanzar el expediente al siguiente estado?")) return;
    setStateLoading("advance");
    try {
      await api.post(`/expedientes/${expedienteId}/admin/advance-state/`, {});
      toast.success("Estado avanzado correctamente");
      onRefresh();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Error al avanzar estado");
    } finally {
      setStateLoading(null);
    }
  };

  const revertState = async () => {
    if (!window.confirm("¿Confirmas retroceder el expediente al estado anterior? Esta acción puede revertir artefactos.")) return;
    setStateLoading("revert");
    try {
      await api.post(`/expedientes/${expedienteId}/admin/revert-state/`, {});
      toast.success("Estado revertido correctamente");
      onRefresh();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Error al revertir estado");
    } finally {
      setStateLoading(null);
    }
  };

  // ── Admin: agregar / quitar tipos de artefactos en el policy ──────────────
  const addArtifactType = async (stateName: string, artifactType: string) => {
    const reg = ARTIFACT_UI_REGISTRY[artifactType];
    try {
      await api.post(`/expedientes/${expedienteId}/admin/policy/add-artifact/`, {
        state: stateName,
        artifact_type: artifactType,
      });
      toast.success(`Artefacto ${artifactType} agregado a ${stateName}`);
      
      // Refresh local data first
      await onRefresh();
      
      // Immediately open the registration modal for the new type
      if (reg) {
        handleExecute(reg.command);
      }
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Error al agregar artefacto");
    }
  };

  const removeArtifactType = async (stateName: string, artifactType: string) => {
    if (!window.confirm(`¿Quitar el artefacto ${artifactType} de la fase ${stateName}?`)) return;
    try {
      await api.post(`/expedientes/${expedienteId}/admin/policy/remove-artifact/`, {
        state: stateName,
        artifact_type: artifactType,
      });
      toast.success(`Artefacto ${artifactType} removido de ${stateName}`);
      onRefresh();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Error al remover artefacto");
    }
  };

  const isLegacy = isLegacyExpediente(expedienteData);
  const currentIdx = CANONICAL_STATES.indexOf(currentState as any);

  // Modern expedientes: show ALL states (so artifacts are always visible even for past states)
  // Mostrar solo los estados del timeline (excluye CANCELADO por defecto)
  // Pero si el estado actual es CANCELADO, lo incluimos para que sea visible.
  const statesToRender = currentState === "CANCELADO" 
    ? CANONICAL_STATES 
    : TIMELINE_STEPS;


  return (
    <div className="space-y-3">
      {/* ── Panel Admin — solo visible para is_superuser ──────────────────── */}
      {isAdmin && (
        <div className="card border border-amber-200 bg-amber-50/40 overflow-hidden">
          <div className="px-5 py-3 border-b border-amber-200 flex items-center gap-2">
            <AlertTriangle size={14} className="text-amber-600" />
            <span className="text-xs font-bold text-amber-700 uppercase tracking-wider">Panel Admin — Solo superusuarios</span>
          </div>
          <div className="px-5 py-4 flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="text-xs text-amber-700 font-medium">Estado actual:</span>
              <span className="font-mono text-xs font-bold text-amber-900 bg-amber-100 px-2 py-0.5 rounded">
                {currentState}
              </span>
            </div>
            <div className="flex items-center gap-2 ml-auto">
              <button
                className="btn btn-sm flex items-center gap-1.5 border border-amber-400 text-amber-700 bg-white hover:bg-amber-50 disabled:opacity-50"
                onClick={revertState}
                disabled={stateLoading !== null || currentState === CANONICAL_STATES[0]}
                title="Retroceder al estado anterior"
              >
                {stateLoading === "revert" ? (
                  <span className="w-3.5 h-3.5 border-2 border-amber-600 border-t-transparent rounded-full animate-spin" />
                ) : (
                  <ArrowLeft size={13} />
                )}
                Retroceder
              </button>
              <button
                className="btn btn-sm flex items-center gap-1.5 border border-amber-500 text-white bg-amber-600 hover:bg-amber-700 disabled:opacity-50"
                onClick={advanceState}
                disabled={
                  stateLoading !== null ||
                  currentState === CANONICAL_STATES[CANONICAL_STATES.length - 1]
                }
                title="Avanzar al siguiente estado"
              >
                {stateLoading === "advance" ? (
                  <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <ArrowRight size={13} />
                )}
                Avanzar
              </button>
            </div>
          </div>
          <p className="px-5 pb-3 text-[10px] text-amber-600 italic">
            Los botones avanzar/retroceder llaman a endpoints de admin en el backend. Úsalos con precaución.
          </p>
        </div>
      )}

      {statesToRender.map((stateName) => {
        const stateIdx = CANONICAL_STATES.indexOf(stateName as any);

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
            .map((type: string) => LEGACY_ARTIFACT_COMMAND_MAP[type])
            .filter(Boolean);
          const hasAvailable = commandsInState.some((cmd: string) => hasAction(cmd));

          return (
            <div key={stateName} className="card">
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
                  {stateArtifactTypes.map((artType: string) => {
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
                  onAddArtifactType={
                    isAdmin
                      ? () => setAddArtifactToState(stateName)
                      : undefined
                  }
                  onRemoveArtifactType={
                    isAdmin
                      ? (artType) => removeArtifactType(stateName, artType)
                      : undefined
                  }
                />
              </div>
            )}
          </div>
        );
      })}

      {activeModal && (
        <ArtifactModal
          open={true}
          expedienteId={expedienteId}
          commandKey={activeModal.commandKey}
          artifact={activeModal.artifact}
          readOnly={activeModal.artifact !== undefined}
          onClose={() => setActiveModal(null)}
          onSuccess={handleSuccess}
          isAdmin={isAdmin}
          allArtifacts={
            // Pass all artifacts of the same type so the History tab works
            activeModal.artifact
              ? (Array.isArray(artifacts) ? artifacts : []).filter(
                  (a: any) => a.artifact_type === activeModal.artifact.artifact_type
                )
              : []
          }
          onNewRecord={
            activeModal.artifact !== undefined
              ? () => setActiveModal({ commandKey: activeModal.commandKey, artifact: undefined })
              : undefined
          }
        />
      )}

      {/* Admin: Modal de selección de artefacto */}
      {isAdmin && (
        <AddArtifactModal
          open={!!addArtifactToState}
          onClose={() => setAddArtifactToState(null)}
          artifacts={artifacts || []}
          onSelect={(artType) => {
            if (addArtifactToState) {
              addArtifactType(addArtifactToState, artType);
              setAddArtifactToState(null);
            }
          }}
        />
      )}

    </div>
  );
}
