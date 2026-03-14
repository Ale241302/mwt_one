'use client';
import { LucideIcon, TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface KPICardProps {
  label: string;
  value: string;
  icon: LucideIcon;
  trend: 'up' | 'down' | 'neutral';
  sub?: string;
}

export function KPICard({ label, value, icon: Icon, trend, sub }: KPICardProps) {
  const TrendIcon =
    trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus;

  const trendStyle: React.CSSProperties =
    trend === 'up'
      ? { color: 'var(--success)' }
      : trend === 'down'
      ? { color: 'var(--coral)' }
      : { color: 'var(--text-disabled)' };

  return (
    <div className="card-mwt p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center"
          style={{ backgroundColor: 'color-mix(in srgb, var(--navy) 8%, transparent)' }}
        >
          <Icon size={16} style={{ color: 'var(--navy)' }} />
        </div>
        <TrendIcon size={14} style={trendStyle} aria-hidden />
      </div>
      <div>
        <p className="text-2xl font-bold font-mono" style={{ color: 'var(--navy)' }}>{value}</p>
        <p className="text-xs mt-0.5" style={{ color: 'var(--text-tertiary)' }}>{label}</p>
        {sub && <p className="text-[11px]" style={{ color: 'var(--text-disabled)' }}>{sub}</p>}
      </div>
    </div>
  );
}
