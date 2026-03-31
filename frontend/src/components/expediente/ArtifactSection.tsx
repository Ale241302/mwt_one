"use client";

import { useState } from "react";
import { Plus, ChevronDown } from "lucide-react";
import ArtifactRow from "./ArtifactRow";
import { ARTIFACT_UI_REGISTRY } from "@/constants/artifact-ui-registry";

export interface ArtifactPolicyState {
  required: string[];
  optional: string[];
  gate_for_advance: string[];
}

interface ArtifactSectionProps {
  policyState: ArtifactPolicyState;
  artifacts: any[];
  availableActions: string[];
  onExecute: (commandKey: string, artifact?: any) => void;
  hasAction: (commandKey: string) => boolean;
}

export default function ArtifactSection({
  policyState,
  artifacts,
  onExecute,
  hasAction,
}: ArtifactSectionProps) {
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const existingTypes = new Set(artifacts.map((a) => a.artifact_type));

  // Partition optional types into existing and pending
  const existingOptionals = policyState.optional.filter((opt) => existingTypes.has(opt));
  const pendingOptionals = policyState.optional.filter((opt) => !existingTypes.has(opt));

  const renderArtifact = (artType: string) => {
    const reg = ARTIFACT_UI_REGISTRY[artType];
    if (!reg) return null;

    const latestArt = artifacts
      .filter((a) => a.artifact_type === artType)
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())[0];

    const isAvailable = hasAction(reg.command);
    const isGate = policyState.gate_for_advance.includes(artType);
    
    // Check if it's completed (ignoring case just in case)
    const isCompleted = latestArt?.status && latestArt.status.toUpperCase() === "COMPLETED";

    const blockReason = isGate && !isCompleted ? "Requerido para avanzar" : undefined;

    return (
      <ArtifactRow
        key={artType}
        artifactType={artType}
        commandKey={reg.command}
        label={reg.label}
        artifact={latestArt}
        isAvailable={isAvailable}
        onExecute={onExecute}
        blockReason={blockReason}
      />
    );
  };

  return (
    <div className="flex flex-col opacity-100">
      {/* Required Artifacts */}
      {policyState.required.map(renderArtifact)}

      {/* Existing Optional Artifacts */}
      {existingOptionals.map(renderArtifact)}

      {/* Pending Optional Artifacts (+ Agregar dropdown) */}
      {pendingOptionals.length > 0 && (
        <div className="px-5 py-3 relative">
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-2 text-sm text-primary font-medium hover:text-primary-dark transition-colors"
          >
            <Plus size={16} /> <span>Agregar Opcional</span>
            <ChevronDown size={14} className={`transition-transform ${dropdownOpen ? "rotate-180" : ""}`} />
          </button>
          
          {dropdownOpen && (
            <div className="absolute top-10 left-5 z-10 bg-surface border border-divider rounded-lg shadow-lg py-1 min-w-[200px]">
              {pendingOptionals.map((opt) => {
                const reg = ARTIFACT_UI_REGISTRY[opt];
                if (!reg) return null;
                const available = hasAction(reg.command);
                return (
                  <button
                    key={opt}
                    onClick={() => {
                      if (available) onExecute(reg.command);
                      setDropdownOpen(false);
                    }}
                    disabled={!available}
                    className={`w-full text-left px-4 py-2 text-sm transition-colors ${
                      available
                        ? "hover:bg-bg cursor-pointer text-text"
                        : "text-text-disabled cursor-not-allowed"
                    }`}
                  >
                    {reg.label}
                  </button>
                );
              })}
            </div>
          )}
        </div>
      )}
      
      {policyState.required.length === 0 && existingOptionals.length === 0 && pendingOptionals.length === 0 && (
        <div className="px-5 py-4 text-sm text-text-tertiary">
          No hay requerimientos en esta fase.
        </div>
      )}
    </div>
  );
}
