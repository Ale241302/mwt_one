"use client";

import { useState, useEffect, useRef } from "react";
import { Plus, ChevronDown, X } from "lucide-react";
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
  /** Admin: agregar un tipo de artefacto opcional a la policy de esta fase */
  onAddArtifactType?: (artifactType: string) => void;
  /** Admin: quitar un tipo de artefacto de la policy de esta fase */
  onRemoveArtifactType?: (artifactType: string) => void;
}

// Todos los tipos opcionales conocidos que se pueden agregar (admin)
const ALL_OPTIONAL_TYPES = Object.keys(ARTIFACT_UI_REGISTRY).filter(
  (k) => !k.startsWith("ART-") || parseInt(k.replace("ART-", ""), 10) >= 10
);

export default function ArtifactSection({
  policyState,
  artifacts,
  onExecute,
  hasAction,
  isAdmin,
  onAddArtifactType,
  onRemoveArtifactType,
}: ArtifactSectionProps) {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [addDropdownOpen, setAddDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const addDropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
      if (addDropdownRef.current && !addDropdownRef.current.contains(e.target as Node)) {
        setAddDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const existingTypes = new Set(artifacts.map((a) => a.artifact_type));

  const existingOptionals = policyState.optional.filter((opt) => existingTypes.has(opt));
  const pendingOptionals = policyState.optional.filter((opt) => !existingTypes.has(opt));

  // Tipos que admin puede agregar: los que no están ya en required ni optional
  const allCurrentTypes = new Set([...policyState.required, ...policyState.optional]);
  const adminAddableTypes = ALL_OPTIONAL_TYPES.filter(
    (t) => !allCurrentTypes.has(t) && ARTIFACT_UI_REGISTRY[t]
  );

  const renderArtifact = (artType: string, isOptional = false) => {
    const reg = ARTIFACT_UI_REGISTRY[artType];
    if (!reg) return null;

    const allOfType = artifacts
      .filter((a) => a.artifact_type === artType)
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

    const latestArt = allOfType[0];
    const isAvailable = hasAction(reg.command);
    const isGate = policyState.gate_for_advance.includes(artType);
    const isCompleted = latestArt?.status && latestArt.status.toUpperCase() === "COMPLETED";
    const blockReason = isGate && !isCompleted ? "Requerido para avanzar" : undefined;

    return (
      <ArtifactRow
        key={artType}
        artifactType={artType}
        commandKey={reg.command}
        label={reg.label}
        artifact={latestArt}
        allArtifacts={allOfType}
        isAvailable={isAvailable}
        onExecute={onExecute}
        blockReason={blockReason}
        isAdmin={isAdmin}
        onRemoveArtifactType={
          isAdmin && isOptional && onRemoveArtifactType
            ? onRemoveArtifactType
            : undefined
        }
      />
    );
  };

  return (
    <div className="flex flex-col opacity-100">
      {/* Artefactos requeridos */}
      {policyState.required.map((t) => renderArtifact(t, false))}

      {/* Opcionales ya creados */}
      {existingOptionals.map((t) => renderArtifact(t, true))}

      {/* Opcionales pendientes: dropdown "+ Agregar Opcional" */}
      {pendingOptionals.length > 0 && (
        <div className="px-5 py-3 relative" ref={dropdownRef}>
          <button
            onClick={() => setDropdownOpen((prev) => !prev)}
            className="flex items-center gap-2 text-sm text-primary font-medium hover:text-primary-dark transition-colors"
          >
            <Plus size={16} />
            <span>Agregar Opcional</span>
            <ChevronDown
              size={14}
              className={`transition-transform ${dropdownOpen ? "rotate-180" : ""}`}
            />
          </button>

          {dropdownOpen && (
            <div className="absolute top-10 left-5 z-20 bg-surface border border-divider rounded-lg shadow-lg py-1 min-w-[240px]">
              {pendingOptionals.map((opt) => {
                const reg = ARTIFACT_UI_REGISTRY[opt];
                if (!reg) return null;
                // Para admin, siempre habilitado aunque hasAction sea false
                const available = hasAction(reg.command) || !!isAdmin;
                return (
                  <button
                    key={opt}
                    onClick={() => {
                      setDropdownOpen(false);
                      onExecute(reg.command, undefined);
                    }}
                    disabled={!available}
                    className={`w-full text-left px-4 py-2 text-sm transition-colors ${
                      available
                        ? "hover:bg-bg cursor-pointer text-text"
                        : "text-text-disabled cursor-not-allowed opacity-50"
                    }`}
                  >
                    <span className="font-mono text-[10px] text-text-tertiary mr-2">{reg.command}</span>
                    {reg.label}
                    {isAdmin && !hasAction(reg.command) && (
                      <span className="ml-2 text-[9px] bg-amber-100 text-amber-700 px-1 rounded">admin</span>
                    )}
                  </button>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Admin: botón para agregar tipos de artefactos extra (fuera del policy actual) */}
      {isAdmin && onAddArtifactType && adminAddableTypes.length > 0 && (
        <div className="px-5 py-2 border-t border-dashed border-amber-200 relative" ref={addDropdownRef}>
          <button
            onClick={() => setAddDropdownOpen((prev) => !prev)}
            className="flex items-center gap-2 text-xs text-amber-600 font-medium hover:text-amber-800 transition-colors"
          >
            <Plus size={13} />
            <span>Agregar artefacto (admin)</span>
            <ChevronDown
              size={12}
              className={`transition-transform ${addDropdownOpen ? "rotate-180" : ""}`}
            />
          </button>

          {addDropdownOpen && (
            <div className="absolute bottom-9 left-5 z-20 bg-surface border border-amber-200 rounded-lg shadow-lg py-1 min-w-[260px] max-h-60 overflow-y-auto">
              <p className="px-3 py-1.5 text-[9px] font-bold text-amber-600 uppercase tracking-wider border-b border-amber-100">
                Solo visible para admin
              </p>
              {adminAddableTypes.map((t) => {
                const reg = ARTIFACT_UI_REGISTRY[t];
                return (
                  <button
                    key={t}
                    onClick={() => {
                      setAddDropdownOpen(false);
                      onAddArtifactType(t);
                    }}
                    className="w-full text-left px-4 py-2 text-sm hover:bg-amber-50 cursor-pointer text-text transition-colors"
                  >
                    <span className="font-mono text-[10px] text-text-tertiary mr-2">{reg.command}</span>
                    {reg.label}
                  </button>
                );
              })}
            </div>
          )}
        </div>
      )}

      {policyState.required.length === 0 &&
        existingOptionals.length === 0 &&
        pendingOptionals.length === 0 && (
          <div className="px-5 py-4 text-sm text-text-tertiary">
            No hay requerimientos en esta fase.
          </div>
        )}
    </div>
  );
}
