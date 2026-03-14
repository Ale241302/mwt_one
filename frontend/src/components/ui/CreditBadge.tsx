'use client';
import { CheckCircle, AlertTriangle, AlertOctagon } from 'lucide-react';
import { CreditBand, CREDIT_BAND_CONFIG } from '@/lib/constants/creditBands';

interface CreditBadgeProps {
  band: CreditBand;
  className?: string;
}

const ICONS = {
  'check-circle': CheckCircle,
  'alert-triangle': AlertTriangle,
  'alert-octagon': AlertOctagon,
} as const;

export function CreditBadge({ band, className = '' }: CreditBadgeProps) {
  const cfg = CREDIT_BAND_CONFIG[band];
  const Icon = ICONS[cfg.icon as keyof typeof ICONS];
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold tracking-[0.5px] uppercase ${className}`}
      style={{ backgroundColor: cfg.bg, color: cfg.text }}
      aria-label={`Semáforo crédito: ${cfg.label}`}
    >
      <Icon size={12} aria-hidden />
      {cfg.label}
    </span>
  );
}
