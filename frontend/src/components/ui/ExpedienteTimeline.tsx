'use client';
import { 
  Check, 
  FileText, 
  Settings, 
  ClipboardList, 
  Package, 
  Truck, 
  MapPin, 
  CheckCircle 
} from 'lucide-react';
import { TIMELINE_STEPS, STATE_LABELS, CanonicalState } from '@/constants/states';
import { cn } from '@/lib/utils';


interface ExpedienteTimelineProps {
  currentState: CanonicalState;
  isCancelled?: boolean;
}

const STATE_ICONS: Record<string, any> = {
  REGISTRO: FileText,
  PRODUCCION: Settings,
  PREPARACION: ClipboardList,
  DESPACHO: Package,
  TRANSITO: Truck,
  EN_DESTINO: MapPin,
  CERRADO: CheckCircle,
};

function getStepStatus(step: CanonicalState, current: CanonicalState): 'completed' | 'active' | 'future' {
  const currentIdx = TIMELINE_STEPS.indexOf(current as any);
  const stepIdx = TIMELINE_STEPS.indexOf(step as any);

  if (stepIdx < currentIdx) return 'completed';
  if (stepIdx === currentIdx) return 'active';
  return 'future';
}

function getStepColor(step: CanonicalState, status: string, isCancelled: boolean) {
  if (isCancelled && status === 'active') return 'bg-red-500 border-red-500';
  if (step === 'EN_DESTINO' && (status === 'active' || status === 'completed')) return 'bg-green-500 border-green-500';
  if (step === 'CERRADO' && (status === 'active' || status === 'completed')) return 'bg-blue-600 border-blue-600';
  
  if (status === 'completed') return 'bg-brand-accent border-brand-accent';
  if (status === 'active') return 'bg-brand-primary border-brand-primary';
  return 'bg-surface border-dashed border-border';
}

export function ExpedienteTimeline({ currentState, isCancelled = false }: ExpedienteTimelineProps) {
  const displaySteps = [...TIMELINE_STEPS];

  return (
    <div className="relative flex items-center gap-0 py-2" role="list" aria-label="Timeline del expediente">
      {displaySteps.map((step, i) => {
        const status = getStepStatus(step, currentState === 'CANCELADO' ? 'REGISTRO' : currentState);
        const Icon = STATE_ICONS[step] || Check;
        const colorClass = getStepColor(step, status, isCancelled);

        return (
          <div key={step} className="flex items-center" role="listitem">
            {/* Icon Container */}
            <div
              aria-label={`${STATE_LABELS[step]}: ${status}`}
              className={cn(
                'flex items-center justify-center rounded-full border-2 transition-all p-1',
                status === 'active' ? 'w-8 h-8 animate-timeline-pulse z-10' : 'w-7 h-7',
                colorClass
              )}
            >
              {status === 'completed' ? (
                <Check size={14} className="text-white" strokeWidth={3} />
              ) : (
                <Icon size={status === 'active' ? 16 : 14} className={cn(status === 'future' ? 'text-text-tertiary' : 'text-white')} />
              )}
            </div>
            {/* Label */}
            <div className="flex flex-col ml-1 mr-2">
              <span
                className={cn(
                  'hidden md:block text-[10px] font-medium leading-tight',
                  status === 'active' ? 'text-text-primary font-bold' : 'text-text-tertiary'
                )}
              >
                {STATE_LABELS[step]}
              </span>
            </div>
            {/* Connector */}
            {i < displaySteps.length - 1 && (
              <div
                className={cn(
                  'mx-1 h-[2px] w-4 lg:w-8',
                  status === 'completed' ? (step === 'EN_DESTINO' ? 'bg-green-500' : 'bg-brand-accent') : 'border-t-2 border-dashed border-border'
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
