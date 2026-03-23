import React from 'react';
import { STATE_LABELS, TIMELINE_STEPS } from '@/lib/constants/states';
import { Check, CircleDot, Circle } from 'lucide-react';

interface StateTimelinePortalProps {
  currentStatus: string;
}

export function StateTimelinePortal({ currentStatus }: StateTimelinePortalProps) {
  const currentIndex = Math.max(0, TIMELINE_STEPS.indexOf(currentStatus as any));

  return (
    <div className="p-6 rounded-2xl mb-8" style={{ 
      background: 'var(--surface-glass-bg)', 
      backdropFilter: 'var(--surface-glass-blur)',
      border: 'var(--surface-glass-border)'
    }}>
      <h3 className="text-lg font-semibold mb-10 text-center" style={{ color: 'var(--text-primary)' }}>Progreso del Expediente</h3>
      
      <div className="flex items-center justify-between relative px-4">
        <div className="absolute left-4 right-4 top-1/2 -translate-y-1/2 h-1 bg-gray-200 rounded-full z-0" />
        <div 
          className="absolute left-4 top-1/2 -translate-y-1/2 h-1 rounded-full z-0 transition-all duration-500" 
          style={{ 
            width: `calc(${(currentIndex / (TIMELINE_STEPS.length - 1)) * 100}% - 32px)`, 
            background: 'var(--mwt-primary)' 
          }}
        />
        
        {TIMELINE_STEPS.map((step, idx) => {
          const isCompleted = idx < currentIndex;
          const isCurrent = idx === currentIndex;
          const label = STATE_LABELS[step as keyof typeof STATE_LABELS] || step;
          
          return (
            <div key={step} className="relative z-10 flex flex-col items-center gap-2">
              <div 
                className={`w-8 h-8 rounded-full flex items-center justify-center transition-colors duration-300
                  ${isCompleted ? 'text-white' : 
                    isCurrent ? 'text-white shadow-[0_0_15px_rgba(59,130,246,0.5)]' : 
                    'bg-white border-2 border-gray-300 text-gray-300'}
                `}
                style={{ 
                  background: isCompleted || isCurrent ? 'var(--mwt-primary)' : 'white'
                }}
              >
                {isCompleted ? <Check size={16} /> : isCurrent ? <CircleDot size={16} /> : <Circle size={12} />}
              </div>
              <span 
                className={`text-xs font-medium whitespace-nowrap absolute -bottom-6
                  ${isCurrent ? 'text-gray-900' : 'text-gray-500'}
                `}
              >
                {label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
