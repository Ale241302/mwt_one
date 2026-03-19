'use client';
import { Check } from 'lucide-react';
import { TIMELINE_STEPS, STATE_LABELS, CanonicalState } from '@/constants/states';
import { cn } from '@/lib/utils';


interface ExpedienteTimelineProps {
  currentState: CanonicalState;
  isCancelled?: boolean;
}

function getStepStatus(step: CanonicalState, current: CanonicalState): 'completed' | 'active' | 'future' {
  const currentIdx = TIMELINE_STEPS.indexOf(current as any);
  const stepIdx = TIMELINE_STEPS.indexOf(step as any);

  if (stepIdx < currentIdx) return 'completed';
  if (stepIdx === currentIdx) return 'active';
  return 'future';
}

export function ExpedienteTimeline({ currentState, isCancelled = false }: ExpedienteTimelineProps) {
  const displaySteps = [...TIMELINE_STEPS];


  return (
    <div className="relative flex items-center gap-0" role="list" aria-label="Timeline del expediente">
      {displaySteps.map((step, i) => {
        const status = getStepStatus(step, currentState === 'CANCELADO' ? 'REGISTRO' : currentState);
        return (
          <div key={step} className="flex items-center" role="listitem">
            {/* Dot */}
            <div
              aria-label={`${STATE_LABELS[step]}: ${status}`}
              className={cn(
                'flex items-center justify-center rounded-full border-2 transition-all',
                status === 'completed' && 'w-4 h-4 bg-brand-accent border-brand-accent',
                status === 'active' && 'w-5 h-5 bg-brand-primary border-brand-primary animate-timeline-pulse',
                status === 'future' && 'w-4 h-4 bg-surface border-dashed border-border'
              )}
            >
              {status === 'completed' && <Check size={9} className="text-white" strokeWidth={3} />}
            </div>
            {/* Label */}
            <span
              className={cn(
                'hidden md:block text-[10px] ml-1 font-medium',
                status === 'active' ? 'text-text-primary font-semibold' : 'text-text-tertiary'
              )}
            >
              {STATE_LABELS[step]}
            </span>
            {/* Connector */}
            {i < displaySteps.length - 1 && (
              <div
                className={cn(
                  'mx-1 h-px flex-1 min-w-[12px]',
                  status === 'completed' ? 'bg-brand-accent' : 'border-t border-dashed border-border'
                )}
              />
            )}
          </div>
        );
      })}

      {/* CANCELADO badge lateral */}
      {isCancelled && (
        <span className="ml-3 badge badge-critical">
          Cancelado
        </span>
      )}
    </div>

  );
}
