'use client';
import Link from 'next/link';
import { AlertTriangle } from 'lucide-react';
import { ExpedienteCard } from './PipelineView';
import { CreditBadge } from '@/components/ui/CreditBadge';

interface PipelineCardProps {
  card: ExpedienteCard;
}

export function PipelineCard({ card }: PipelineCardProps) {
  return (
    <Link href={`/expedientes/${card.id}`}>
      <div
        className={[
          'card-mwt p-3 cursor-pointer hover:shadow-md transition-shadow',
          card.is_blocked ? 'border-l-4 border-l-red-500' : '',
        ].join(' ')}
      >
        {/* Ref */}
        <div className="flex items-center justify-between mb-1.5">
          <span className="font-mono text-xs font-medium text-[#013A57]">{card.ref}</span>
          {card.is_blocked && (
            <span className="inline-flex items-center gap-0.5 text-[10px] font-semibold uppercase tracking-[0.5px] text-red-600 bg-red-50 px-1.5 py-0.5 rounded">
              <AlertTriangle size={9} />
              Bloqueado
            </span>
          )}
        </div>

        {/* Client */}
        <p className="text-xs text-slate-600 mb-1 truncate">{card.client}</p>

        {/* Brand pill */}
        <span
          className="inline-block text-[10px] font-semibold px-2 py-0.5 rounded-full uppercase tracking-[0.5px] mb-2"
          style={{
            background: card.brand_color ? `${card.brand_color}20` : '#F1F5F9',
            color: card.brand_color ?? '#475569',
          }}
        >
          {card.brand}
        </span>

        {/* Credit semaphore — SIEMPRE color + texto + ícono */}
        <CreditBadge band={card.credit_band} />

        {/* Artifact progress dots */}
        <div className="flex items-center gap-1 mt-2">
          {Array.from({ length: card.artifacts_total }).map((_, i) => (
            <span
              key={i}
              className={`inline-block w-2 h-2 rounded-full ${
                i < card.artifacts_done ? 'bg-[#75CBB3]' : 'bg-slate-200'
              }`}
              aria-hidden
            />
          ))}
          <span className="text-[10px] text-slate-400 ml-1">
            {card.artifacts_done}/{card.artifacts_total}
          </span>
        </div>

        {/* Pending action */}
        {card.pending_action && (
          <p className="text-[11px] italic text-slate-400 mt-1.5 truncate">
            {card.pending_action}
          </p>
        )}
      </div>
    </Link>
  );
}
