'use client';
import { useState } from 'react';
import { ChevronDown, ChevronRight, Check, Clock, XCircle } from 'lucide-react';
import { CanonicalState, STATE_LABELS, TIMELINE_STEPS } from '@/lib/constants/states';

export type ArtifactStatus = 'done' | 'pending' | 'blocked';

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

const STATUS_ICON = {
  done:    <Check size={14} className="text-[#0E8A6D]" />,
  pending: <Clock size={14} className="text-[#B45309]" />,
  blocked: <XCircle size={14} className="text-[#DC2626]" />,
};

const STATUS_LABEL = { done: 'Completado', pending: 'Pendiente', blocked: 'Bloqueado' };

interface ArtifactAccordionProps {
  sections: StateSection[];
  currentState: CanonicalState;
  onRegister: (artifactId: string) => void;
}

export function ArtifactAccordion({ sections, currentState, onRegister }: ArtifactAccordionProps) {
  const [openStates, setOpenStates] = useState<Set<CanonicalState>>(new Set([currentState]));

  const toggle = (state: CanonicalState) => {
    setOpenStates(prev => {
      const next = new Set(prev);
      next.has(state) ? next.delete(state) : next.add(state);
      return next;
    });
  };

  const currentIdx = TIMELINE_STEPS.indexOf(currentState);

  return (
    <div className="flex flex-col gap-2">
      {sections.map(section => {
        const sectionIdx = TIMELINE_STEPS.indexOf(section.state);
        const sectionStatus =
          sectionIdx < currentIdx ? 'completed' :
          sectionIdx === currentIdx ? 'active' : 'future';
        const isOpen = openStates.has(section.state);

        return (
          <div
            key={section.state}
            className={`border rounded-xl overflow-hidden transition-all ${
              sectionStatus === 'active'
                ? 'border-[#013A57]/20 shadow-sm'
                : 'border-slate-200'
            }`}
          >
            {/* Accordion header */}
            <button
              onClick={() => toggle(section.state)}
              className={`w-full flex items-center justify-between px-4 py-3 text-left ${
                sectionStatus === 'active' ? 'bg-[#013A57]/5' : 'bg-white'
              }`}
              aria-expanded={isOpen}
            >
              <div className="flex items-center gap-2">
                <div
                  className={`w-2 h-2 rounded-full ${
                    sectionStatus === 'completed' ? 'bg-[#75CBB3]' :
                    sectionStatus === 'active' ? 'bg-[#013A57] animate-timeline-pulse' :
                    'bg-slate-200'
                  }`}
                />
                <span className={`text-sm font-semibold ${
                  sectionStatus === 'active' ? 'text-[#013A57]' :
                  sectionStatus === 'completed' ? 'text-slate-500' : 'text-slate-400'
                }`}>
                  {STATE_LABELS[section.state]}
                </span>
                {sectionStatus === 'completed' && (
                  <span className="text-xs text-slate-400">
                    {section.completedCount}/{section.artifacts.length} completos
                  </span>
                )}
                {sectionStatus === 'future' && (
                  <span className="text-xs text-slate-400">Pendiente</span>
                )}
              </div>
              {isOpen ? <ChevronDown size={16} className="text-slate-400" /> :
                        <ChevronRight size={16} className="text-slate-400" />}
            </button>

            {/* Accordion body */}
            {isOpen && (
              <div className="px-4 pb-4 bg-white">
                <div className="flex flex-col gap-1 mt-2">
                  {section.artifacts.map(art => (
                    <div
                      key={art.id}
                      className={`flex items-start justify-between p-2.5 rounded-lg ${
                        art.is_next ? 'bg-blue-50 border border-blue-200' : 'hover:bg-slate-50'
                      }`}
                    >
                      <div className="flex items-start gap-2">
                        <span className="mt-0.5">{STATUS_ICON[art.status]}</span>
                        <div>
                          <p className={`text-sm font-medium ${
                            art.is_next ? 'text-blue-700' : 'text-slate-700'
                          }`}>
                            {art.name}
                          </p>
                          {art.description && (
                            <p className="text-xs text-slate-400 mt-0.5">{art.description}</p>
                          )}
                          <span className="text-[10px] text-slate-400">{STATUS_LABEL[art.status]}</span>
                        </div>
                      </div>

                      {art.is_next && art.status !== 'done' && (
                        <button
                          onClick={() => onRegister(art.id)}
                          className="ml-2 shrink-0 text-xs font-semibold px-3 py-1.5 rounded-lg bg-[#013A57] text-white hover:bg-[#0A4F75] transition-colors"
                        >
                          Registrar
                        </button>
                      )}
                    </div>
                  ))}
                </div>

                {/* Gate de avance */}
                {sectionStatus === 'active' && section.artifacts.some(a => a.status !== 'done') && (
                  <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                    <p className="text-xs font-medium text-amber-700">
                      Para avanzar a {STATE_LABELS[TIMELINE_STEPS[currentIdx + 1] as CanonicalState] ?? 'siguiente estado'}:
                      completa todos los artefactos de esta fase.
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
