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
  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus;
  const trendColor = trend === 'up' ? 'text-[#0E8A6D]' : trend === 'down' ? 'text-[#DC2626]' : 'text-slate-400';

  return (
    <div className="card-mwt p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div className="w-8 h-8 rounded-lg bg-[#013A57]/8 flex items-center justify-center">
          <Icon size={16} className="text-[#013A57]" />
        </div>
        <TrendIcon size={14} className={trendColor} />
      </div>
      <div>
        <p className="text-2xl font-bold text-[#013A57] font-mono">{value}</p>
        <p className="text-xs text-slate-500 mt-0.5">{label}</p>
        {sub && <p className="text-[11px] text-slate-400">{sub}</p>}
      </div>
    </div>
  );
}
