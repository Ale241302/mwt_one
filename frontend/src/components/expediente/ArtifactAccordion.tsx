"use client";
import { useState } from "react";
import { ChevronDown, ChevronRight, Check, Clock, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { CanonicalState, STATE_LABELS, TIMELINE_STEPS } from "@/lib/constants/states";

export type ArtifactStatus = "done" | "pending" | "blocked";

export interface Artifact {
  id: string;
  name: string;
  description?: string;
  status: ArtifactStatus;
  is_next?: boolean;
}

export interface StateSection {
  state: CanonicalState;
  artifacts: Artifact[];
  completedCount: number;
}

const STATUS_ICON: Record<ArtifactStatus, React.ReactNode> = {
  done:    <Check    size={14} style={{ color: "var(--success)" }}  aria-hidden />,
  pending: <Clock    size={14} style={{ color: "var(--amber)" }}    aria-hidden />,
  blocked: <XCircle  size={14} style={{ color: "var(--coral)" }}   aria-hidden />,
};

const STATUS_LABEL: Record<ArtifactStatus, string> = {
  done:    "Completado",
  pending: "Pendiente",
  blocked: "Bloqueado",
};

interface ArtifactAccordionProps {
  sections: StateSection[];
  currentState: CanonicalState;
  onRegister: (artifactId: string) => void;
}

export function ArtifactAccordion({ sections, currentState, onRegister }: ArtifactAccordionProps) {
  const [openStates, setOpenStates] = useState<Set<CanonicalState>>(new Set([currentState]));

  const toggle = (state: CanonicalState) => {
    setOpenStates((prev) => {
      const next = new Set(prev);
      next.has(state) ? next.delete(state) : next.add(state);
      return next;
    });
  };

  const currentIdx = TIMELINE_STEPS.indexOf(currentState);

  return (
    <div className="flex flex-col gap-2">
      {sections.map((section) => {
        const sectionIdx = TIMELINE_STEPS.indexOf(section.state);
        const sectionStatus =
          sectionIdx < currentIdx ? "completed" :
          sectionIdx === currentIdx ? "active" : "future";
        const isOpen = openStates.has(section.state);

        return (
          <div
            key={section.state}
            className={cn(
              "border rounded-xl overflow-hidden transition-all",
              sectionStatus === "active"
                ? "border-[var(--navy)]/20 shadow-[var(--shadow-sm)]"
                : "border-[var(--border)]"
            )}
          >
            {/* ── Accordion header ── */}
            <button
              onClick={() => toggle(section.state)}
              aria-expanded={isOpen}
              aria-controls={`accordion-body-${section.state}`}
              className={cn(
                "w-full flex items-center justify-between px-4 py-3 text-left transition-colors",
                sectionStatus === "active"
                  ? "bg-[var(--navy)]/5 hover:bg-[var(--navy)]/8"
                  : "bg-[var(--surface)] hover:bg-[var(--surface-hover)]"
              )}
            >
              <div className="flex items-center gap-2">
                {/* Indicador visual */}
                <div
                  className={cn(
                    "w-2 h-2 rounded-full flex-shrink-0",
                    sectionStatus === "completed" ? "bg-[var(--mint)]"
                    : sectionStatus === "active"  ? "bg-[var(--navy)] animate-timeline-pulse"
                    : "bg-[var(--border-strong)]"
                  )}
                />
                <span
                  className={cn(
                    "text-sm font-semibold",
                    sectionStatus === "active"    ? "text-[var(--navy)]"
                    : sectionStatus === "completed" ? "text-[var(--text-tertiary)]"
                    : "text-[var(--text-disabled)]"
                  )}
                >
                  {STATE_LABELS[section.state]}
                </span>
                {sectionStatus === "completed" && (
                  <span className="text-xs text-[var(--text-disabled)]">
                    {section.completedCount}/{section.artifacts.length} completos
                  </span>
                )}
                {sectionStatus === "future" && (
                  <span className="text-xs text-[var(--text-disabled)]">Pendiente</span>
                )}
              </div>
              {isOpen
                ? <ChevronDown  size={16} className="text-[var(--text-tertiary)]" aria-hidden />
                : <ChevronRight size={16} className="text-[var(--text-tertiary)]" aria-hidden />}
            </button>

            {/* ── Accordion body ── */}
            {isOpen && (
              <div id={`accordion-body-${section.state}`} className="px-4 pb-4 bg-[var(--surface)]">
                <div className="flex flex-col gap-1 mt-2">
                  {section.artifacts.map((art) => (
                    <div
                      key={art.id}
                      className={cn(
                        "flex items-start justify-between p-2.5 rounded-lg transition-colors",
                        art.is_next
                          ? "bg-[var(--ice-soft)] border border-[var(--ice)]"
                          : "hover:bg-[var(--surface-hover)]"
                      )}
                    >
                      <div className="flex items-start gap-2">
                        <span className="mt-0.5">{STATUS_ICON[art.status]}</span>
                        <div>
                          <p className={cn(
                            "text-sm font-medium",
                            art.is_next ? "text-[var(--navy)]" : "text-[var(--text-secondary)]"
                          )}>
                            {art.name}
                          </p>
                          {art.description && (
                            <p className="text-xs text-[var(--text-tertiary)] mt-0.5">{art.description}</p>
                          )}
                          <span className="text-[10px] text-[var(--text-disabled)]">
                            {STATUS_LABEL[art.status]}
                          </span>
                        </div>
                      </div>

                      {art.is_next && art.status !== "done" && (
                        <button
                          onClick={() => onRegister(art.id)}
                          className="ml-2 shrink-0 text-xs font-semibold px-3 py-1.5 rounded-lg bg-[var(--navy)] text-[var(--text-inverse)] hover:bg-[var(--navy-light)] transition-colors"
                        >
                          Registrar
                        </button>
                      )}
                    </div>
                  ))}
                </div>

                {/* Gate de avance */}
                {sectionStatus === "active" && section.artifacts.some((a) => a.status !== "done") && (
                  <div className="mt-3 p-3 bg-[var(--amber-soft)] border border-[var(--amber)]/30 rounded-lg">
                    <p className="text-xs font-medium text-[var(--amber)]">
                      Para avanzar a{" "}
                      {STATE_LABELS[TIMELINE_STEPS[currentIdx + 1] as CanonicalState] ?? "siguiente estado"}:
                      {" "}completa todos los artefactos de esta fase.
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
