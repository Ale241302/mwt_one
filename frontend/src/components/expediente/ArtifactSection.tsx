"use client";

import { useState, useEffect, useRef } from "react";
import { Plus } from "lucide-react";
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
  isAdmin?: boolean;
  /** Admin: agregar un tipo de artefacto al custom_policy de esta fase */
  onAddArtifactType?: (artifactType: string) => void;
  /** Admin: quitar un tipo de artefacto de la policy de esta fase */
  onRemoveArtifactType?: (artifactType: string) => void;
  builderContext?: any[];
}

// Helper: all artifact types present in the registry
const ALL_REGISTRY_TYPES = Object.keys(ARTIFACT_UI_REGISTRY);

export default function ArtifactSection({
  policyState,
  artifacts,
  onExecute,
  hasAction,
  isAdmin,
  onAddArtifactType,
  onRemoveArtifactType,
  builderContext,
}: ArtifactSectionProps) {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const policyTypes = new Set([...policyState.required, ...policyState.optional]);

  // Artifact types that already have at least one record
  const existingTypes = new Set(artifacts.map((a) => a.artifact_type));

  // — Required artifacts (always shown)
  const requiredTypes = policyState.required;

  // — Optional artifacts: they are ALL shown as rows in 'Modo Libre' if they are in the policy
  const activeOptionals = policyState.optional;



  const renderArtifact = (artType: string, isOptional = false) => {
    const reg = ARTIFACT_UI_REGISTRY[artType];

    // Fallback display for unknown artifact types (admin-added custom ones)
    let label = reg?.label;
    let command = reg?.command ?? artType;
    
    if (!label) {
      if (builderContext) {
        const found = builderContext.find(b => b.id.toString() === artType || b.title.startsWith(artType));
        if (found) {
          label = found.title;
        } else {
          label = artType;
        }
      } else {
        label = artType;
      }
    }

    // All records of this type, newest first
    const allOfType = artifacts
      .filter((a) => a.artifact_type === artType)
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

    const latestArt = allOfType[0];
    const recordCount = allOfType.length;
    const isAvailable = reg ? hasAction(reg.command) : false;
    const isGate = policyState.gate_for_advance.includes(artType);
    const isCompleted = latestArt?.status &&
      (latestArt.status.toUpperCase() === "COMPLETED");
    const blockReason = isGate && !isCompleted ? "Requerido para avanzar" : undefined;

    return (
      <ArtifactRow
        key={artType}
        artifactType={artType}
        commandKey={command}
        label={label}
        artifact={latestArt}
        allArtifacts={allOfType}
        recordCount={recordCount}
        isAvailable={isAvailable}
        onExecute={onExecute}
        blockReason={blockReason}
        isAdmin={isAdmin}
        onRemoveArtifactType={
          isAdmin && onRemoveArtifactType
            ? onRemoveArtifactType
            : undefined
        }
      />
    );
  };

  const hasAnything =
    policyState.required.length > 0 ||
    activeOptionals.length > 0;

  return (
    <div className="flex flex-col opacity-100">
      {/* Artefactos requeridos */}
      {policyState.required.map((t) => renderArtifact(t, false))}

      {/* Opcionales (que ya tienen registros o están en la política) */}
      {activeOptionals.map((t) => renderArtifact(t, true))}


      {/* Admin: botón para abrir el modal de selección */}
      {isAdmin && onAddArtifactType && (
        <div className="px-5 py-2 border-t border-dashed border-amber-200">
          <button
            onClick={() => onAddArtifactType("")} // We'll repurpose this or use a new prop
            className="flex items-center gap-2 text-xs text-amber-600 font-medium hover:text-amber-800 transition-colors group"
          >
            <div className="w-5 h-5 rounded-full bg-amber-50 flex items-center justify-center group-hover:bg-amber-100 transition-colors">
              <Plus size={13} />
            </div>
            <span>Agregar artefacto (admin)</span>
          </button>
        </div>
      )}

      {/* Empty state */}
      {!hasAnything && (
        <div className="px-5 py-4 text-sm text-text-tertiary">
          No hay artefactos definidos en esta fase.
          {isAdmin && " Usa el botón admin para agregar."}
        </div>
      )}
    </div>
  );
}
