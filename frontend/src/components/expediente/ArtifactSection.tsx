"use client";

import { useState, useEffect, useRef } from "react";
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
  isAdmin?: boolean;
}

export default function ArtifactSection({
  policyState,
  artifacts,
  onExecute,
  hasAction,
  isAdmin,
}: ArtifactSectionProps) {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Cerrar dropdown al hacer click fuera
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    };
    if (dropdownOpen) document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [dropdownOpen]);

  const existingTypes = new Set(artifacts.map((a) => a.artifact_type));

  // Opcionales: ya creados vs pendientes
  const existingOptionals = policyState.optional.filter((opt) => existingTypes.has(opt));
  const pendingOptionals = policyState.optional.filter((opt) => !existingTypes.has(opt));

  const renderArtifact = (artType: string) => {
    const reg = ARTIFACT_UI_REGISTRY[artType];
    if (!reg) return null;

    // Todos los artefactos de este tipo, ordenados por fecha descendente
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
      />
    );
  };

  return (
    <div className="flex flex-col opacity-100">
      {/* Artefactos requeridos */}
      {policyState.required.map(renderArtifact)}

      {/* Opcionales ya creados */}
      {existingOptionals.map(renderArtifact)}

      {/* Dropdown "+ Agregar Opcional" — solo si hay opcionales pendientes */}
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
            <div className="absolute top-10 left-5 z-20 bg-surface border border-divider rounded-lg shadow-lg py-1 min-w-[220px]">
              {pendingOptionals.map((opt) => {
                const reg = ARTIFACT_UI_REGISTRY[opt];
                if (!reg) return null;
                const available = hasAction(reg.command);
                return (
                  <button
                    key={opt}
                    onClick={() => {
                      setDropdownOpen(false);
                      // Siempre intentar abrir — el padre decide si está disponible
                      onExecute(reg.command, undefined);
                    }}
                    disabled={!available}
                    className={`w-full text-left px-4 py-2 text-sm transition-colors ${
                      available
                        ? "hover:bg-bg cursor-pointer text-text"
                        : "text-text-disabled cursor-not-allowed opacity-50"
                    }`}
                  >
                    {reg.label}
                    {!available && (
                      <span className="ml-2 text-[10px] text-text-tertiary">(no disponible)</span>
                    )}
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
