'use client';
import { Check } from 'lucide-react';
import { TIMELINE_STEPS, STATE_LABELS, CanonicalState } from '@/lib/constants/states';

interface ExpedienteTimelineProps {
  currentState: CanonicalState;
  isCancelled?: boolean;
}

function getStepStatus(step: CanonicalState, current: CanonicalState): 'completed' | 'active' | 'future' {
  const currentIdx = TIMELINE_STEPS.indexOf(current);
  const stepIdx    = TIMELINE_STEPS.indexOf(step);
  if (stepIdx < currentIdx)  return 'completed';
  if (stepIdx === currentIdx) return 'active';
  return 'future';
}

export function ExpedienteTimeline({ currentState, isCancelled = false }: ExpedienteTimelineProps) {
  const displaySteps = TIMELINE_STEPS.filter(s => s !== 'CANCELADO');

  return (
    <div className="relative flex items-center gap-0" role="list" aria-label="Timeline del expediente">
      {displaySteps.map((step, i) => {
        const status = getStepStatus(
          step,
          currentState === 'CANCELADO' ? 'REGISTRO' : currentState
        );

        return (
          <div key={step} className="flex items-center" role="listitem">
            {/* Dot */}
            <div
              aria-label={`${STATE_LABELS[step]}: ${status}`}
              className={[
                'flex items-center justify-center rounded-full border-2 transition-all',
                status === 'completed'
                  ? 'w-4 h-4 bg-[var(--mint)]   border-[var(--mint)]'
                  : '',
                status === 'active'
                  ? 'w-5 h-5 bg-[var(--navy)]   border-[var(--navy)]   animate-timeline-pulse'
                  : '',
                status === 'future'
                  ? 'w-4 h-4 bg-[var(--surface)] border-dashed border-[var(--border-strong)]'
                  : '',
              ].join(' ')}
            >
              {status === 'completed' && (
                <Check size={9} color="white" strokeWidth={3} />
              )}
            </div>

            {/* Label */}
            <span
              className={[
                'hidden md:block text-[10px] ml-1 font-medium',
                status === 'active'
                  ? 'text-[var(--navy)] font-semibold'
                  : 'text-[var(--text-disabled)]',
              ].join(' ')}
            >
              {STATE_LABELS[step]}
            </span>

            {/* Connector line */}
            {i < displaySteps.length - 1 && (
              <div
                className={`mx-1 h-px flex-1 min-w-[12px] ${
                  status === 'completed'
                    ? 'bg-[var(--mint)]'
                    : 'border-t border-dashed border-[var(--border-strong)]'
                }`}
              />
            )}
          </div>
        );
      })}

      {/* CANCELADO badge */}
      {isCancelled && (
        <span
          className="ml-3 inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold tracking-[0.5px] uppercase"
          style={{
            background: 'var(--coral-soft)',
            color: 'var(--coral)',
            border: '1px solid color-mix(in srgb, var(--coral) 30%, transparent)',
          }}
        >
          Cancelado
        </span>
      )}
    </div>
  );
}
