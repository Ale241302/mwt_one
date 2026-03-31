"use client";
/**
 * S10-03 — Detalle expediente con acordeón de artefactos y estados canónicos.
 * Renders exactly the 7 canonical states.
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
  LEGACY_ARTIFACT_LABELS 
} from "@/app/[lang]/(mwt)/(dashboard)/expedientes/[id]/legacy-artifacts";

interface Artifact {
  artifact_type: string;
  status: string;
  created_at: string;
}

interface ExpedienteAccordionProps {
  expedienteId: string;
  expedienteData: any; // Full expediente data for policy context
  artifacts: Artifact[];
  availableActions: {
    primary: any[];
    secondary: any[];
    ops: any[];
  } | string[]; // Support both for safety during transition
  onRefresh: () => void;
  currentState: string;
  onActionClick?: (commandKey: string, artifact?: any) => void;
}

export default function ExpedienteAccordion({
  expedienteId, expedienteData, artifacts, availableActions, onRefresh, currentState, onActionClick
}: ExpedienteAccordionProps) {
  // Helper to check if a command is available
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

  // Open current state by default
  const [openPhases, setOpenPhases] = useState<Record<string, boolean>>({ [currentState]: true });

  const [activeModal, setActiveModal] = useState<string | null>(null);

  const toggle = (label: string) =>
    setOpenPhases((prev) => ({ ...prev, [label]: !prev[label] }));

  const isLegacy = isLegacyExpediente(expedienteData);
  const currentIdx = CANONICAL_STATES.indexOf(currentState as any);

  const statesToRender = isLegacy 
    ? CANONICAL_STATES 
    : CANONICAL_STATES.filter((_, idx) => idx <= currentIdx);

  return (
    <div className="space-y-3">
      {statesToRender.map((stateName) => {
        const stateIdx = CANONICAL_STATES.indexOf(stateName as any);
        
        // S20B-10: Hide FUTURE states if not legacy
        if (!isLegacy && stateIdx > currentIdx) return null;

        const isOpen = !!openPhases[stateName];
        
        // Legacy Rendering logic
        if (isLegacy) {
          const stateArtifactTypes = Array.isArray(LEGACY_STATE_ARTIFACTS[stateName]) ? LEGACY_STATE_ARTIFACTS[stateName] : [];
          if (stateName === "CERRADO" && stateArtifactTypes.length === 0) return null;

          const phaseArtifacts = (Array.isArray(artifacts) ? artifacts : []).filter(a => stateArtifactTypes.includes(a.artifact_type));
          const completedCount = phaseArtifacts.filter((a) => a.status === "completed").length;
          
          const commandsInState = stateArtifactTypes.map(type => LEGACY_ARTIFACT_COMMAND_MAP[type]).filter(Boolean);
          const hasAvailable = !!(commandsInState.some(cmd => hasAction(cmd)));

          return (
            <div key={stateName} className="card overflow-hidden">
              <button
                className="w-full flex items-center justify-between px-5 py-3 hover:bg-bg transition-colors"
                onClick={() => toggle(stateName)}
                aria-expanded={isOpen}
              >
                <div className="flex items-center gap-3">
                  <span className="heading-sm font-semibold text-navy">{stateName}</span>
                  <span className="caption text-text-tertiary">{completedCount} / {stateArtifactTypes.length} completados</span>
                  {hasAvailable && (
                    <span className="badge badge-info text-[10px]">Acción disponible</span>
                  )}
                </div>
                {isOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
              </button>

              {isOpen && stateArtifactTypes.length > 0 && (
                <div className="border-t border-divider divide-y divide-divider">
                  {stateArtifactTypes.map(artType => {
                    const cmdKey = LEGACY_ARTIFACT_COMMAND_MAP[artType];
                    if (!cmdKey) return null;

                    const latestArt = (Array.isArray(artifacts) ? artifacts : []).filter(a => a.artifact_type === artType).sort(
                      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
                    )[0];
                    
                    const isAvailable = hasAction(cmdKey);

                    return (
                      <ArtifactRow
                        key={artType}
                        artifactType={artType}
                        commandKey={cmdKey}
                        label={LEGACY_ARTIFACT_LABELS[artType] ?? artType}
                        artifact={latestArt as any}
                        isAvailable={isAvailable}
                        onExecute={onActionClick ?? (() => {})}
                      />
                    );
                  })}
                </div>
              )}
            </div>
          );
        }

        // Modern Policy-Driven Rendering Logic
        const policyForState = expedienteData?.artifact_policy[stateName];
        const stateArtifactTypes = [
          ...policyForState.required,
          ...policyForState.optional
        ];
        
        if (stateArtifactTypes.length === 0 && stateName === "CERRADO") return null;

        const phaseArtifacts = (Array.isArray(artifacts) ? artifacts : []).filter(a => stateArtifactTypes.includes(a.artifact_type));
        const completedCount = phaseArtifacts.filter((a) => a.status && a.status.toUpperCase() === "COMPLETED").length;
        // In the modern view, we don't have a direct commandsInState map. ArtifactSection determines availability.
        // We'll trust the user has an action if there's any pending required or optional component. 
        // For simplicity, we just won't show the generic "Acción disponible" badge on the header when using the modern view (ArtifactSection does indicating).

        return (
          <div key={stateName} className="card overflow-hidden">
            <button
              className="w-full flex items-center justify-between px-5 py-3 hover:bg-bg transition-colors"
              onClick={() => toggle(stateName)}
              aria-expanded={isOpen}
            >
              <div className="flex items-center gap-3">
                <span className="heading-sm font-semibold text-navy">{stateName} {stateIdx < currentIdx && <span className="text-success ml-2">✓</span>}</span>
                <span className="caption text-text-tertiary">{completedCount} completados</span>
              </div>
              {isOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            </button>

            {isOpen && (
              <div className="border-t border-divider">
                <ArtifactSection
                  policyState={policyForState}
                  artifacts={artifacts}
                  availableActions={availableActions as any}
                  onExecute={onActionClick ?? (() => {})}
                  hasAction={hasAction}
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
          commandKey={activeModal}
          onClose={() => setActiveModal(null)}
          onSuccess={onRefresh}
        />
      )}
    </div>
  );
}
