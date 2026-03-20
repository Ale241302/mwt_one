"use client";
/**
 * S10-03 — Detalle expediente con acordeón de artefactos y estados canónicos.
 * Renders exactly the 7 canonical states.
 */
import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import ArtifactModal from "./ArtifactModal";
import ArtifactRow from "./ArtifactRow";
import { CANONICAL_STATES } from "@/constants/states";

interface Artifact {
  artifact_type: string;
  status: string;
  created_at: string;
}

interface ExpedienteAccordionProps {
  expedienteId: string;
  artifacts: Artifact[];
  availableActions: {
    primary: any[];
    secondary: any[];
    ops: any[];
  } | string[]; // Support both for safety during transition
  onRefresh: () => void;
  currentState: string;
}

const STATE_ARTIFACTS: Record<string, string[]> = {
  "REGISTRO": ["ART-01", "ART-02"],
  "PREPARACION": ["ART-03", "ART-07", "ART-08"],
  "PRODUCCION": ["ART-04", "ART-19"],
  "DESPACHO": ["ART-05", "ART-06"],
  "TRANSITO": ["ART-10"],
  "EN_DESTINO": ["ART-09"],
  "CERRADO": []
};

const ARTIFACT_COMMAND_MAP: Record<string, string> = {
  "ART-01": "C2", "ART-02": "C3", "ART-03": "C4",
  "ART-04": "C5", "ART-05": "C6", "ART-06": "C7",
  "ART-07": "C8", "ART-08": "C9", "ART-09": "C13",
  "ART-10": "C22", "ART-19": "C30",
};

const ARTIFACT_LABELS: Record<string, string> = {
  "ART-01": "Orden de Compra", "ART-02": "Proforma", "ART-03": "Decisión Modal",
  "ART-04": "SAP Confirmado",  "ART-05": "Confirmación Producción", "ART-06": "Embarque",
  "ART-07": "Cotización Flete","ART-08": "Aduana", "ART-09": "Factura MWT",
  "ART-10": "Factura Comisión", "ART-19": "Materialización Logística",
};

export default function ExpedienteAccordion({
  expedienteId, artifacts, availableActions, onRefresh, currentState
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

  return (
    <div className="space-y-3">
      {Array.isArray(CANONICAL_STATES) && CANONICAL_STATES.map((stateName) => {
        const isOpen = !!openPhases[stateName];
        const stateArtifactTypes = Array.isArray(STATE_ARTIFACTS[stateName]) ? STATE_ARTIFACTS[stateName] : [];
        
        // Hide CERRADO if no artifacts to show (which there normally aren't any)
        if (stateName === "CERRADO" && stateArtifactTypes.length === 0) return null;

        const phaseArtifacts = (Array.isArray(artifacts) ? artifacts : []).filter(a => stateArtifactTypes.includes(a.artifact_type));
        const completedCount = phaseArtifacts.filter((a) => a.status === "completed").length;
        
        const commandsInState = stateArtifactTypes.map(type => ARTIFACT_COMMAND_MAP[type]).filter(Boolean);
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
                  const cmdKey = ARTIFACT_COMMAND_MAP[artType];
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
                      label={ARTIFACT_LABELS[artType] ?? artType}
                      artifact={latestArt as any}
                      isAvailable={isAvailable}
                      onExecute={setActiveModal}
                    />
                  );
                })}
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
