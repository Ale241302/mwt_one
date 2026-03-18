'use client';
import { Check } from 'lucide-react';
import { TIMELINE_STEPS, STATE_LABELS, CanonicalState } from '@/lib/constants/states';

interface ExpedienteTimelineProps {
  currentState: CanonicalState;
  isCancelled?: boolean;
}

function getStepStatus(step: CanonicalState, current: CanonicalState): 'completed' | 'active' | 'future' {
  const currentIdx = TIMELINE_STEPS.indexOf(current);
  const stepIdx = TIMELINE_STEPS.indexOf(step);
  if (stepIdx < currentIdx) return 'completed';
  if (stepIdx === currentIdx) return 'active';
  return 'future';
}

export function ExpedienteTimeline({ currentState, isCancelled = false }: ExpedienteTimelineProps) {
  const displaySteps = TIMELINE_STEPS.filter(s => s !== 'CANCELADO');

  return (
    <div className="relative flex items-center gap-0" role="list" aria-label="Timeline del expediente">
      {displaySteps.map((step, i) => {
        const status = getStepStatus(step, currentState === 'CANCELADO' ? 'REGISTRO' : currentState);
        return (
          <div key={step} className="flex items-center" role="listitem">
            {/* Dot */}
            <div
              aria-label={`${STATE_LABELS[step]}: ${status}`}
              className={[
                'flex items-center justify-center rounded-full border-2 transition-all',
                status === 'completed' ? 'w-4 h-4 bg-brand-accent border-brand-accent' : '',
                status === 'active'
                  ? 'w-5 h-5 bg-brand-primary border-brand-primary animate-timeline-pulse'
                  : '',
                status === 'future' ? 'w-4 h-4 bg-white border-dashed border-slate-300' : '',
              ].join(' ')}
            >
              {status === 'completed' && <Check size={9} color="white" strokeWidth={3} />}
            </div>
            {/* Label */}
            <span
              className={[
                'hidden md:block text-[10px] ml-1 font-medium',
                status === 'active' ? 'text-brand-primary font-semibold' : 'text-slate-400',
              ].join(' ')}
            >
              {STATE_LABELS[step]}
            </span>
            {/* Connector */}
            {i < displaySteps.length - 1 && (
              <div
                className={`mx-1 h-px flex-1 min-w-[12px] ${
                  status === 'completed' ? 'bg-brand-accent' : 'border-t border-dashed border-slate-300'
                }`}
              />
            )}
          </div>
        );
      })}

      {/* CANCELADO badge lateral */}
      {isCancelled && (
        <span className="ml-3 inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold tracking-[0.5px] uppercase bg-red-50 text-red-600 border border-red-200">
          Cancelado
        </span>
      )}
    </div>
  );
}
