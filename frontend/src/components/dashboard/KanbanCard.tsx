import React from 'react';
import { Clock, AlertTriangle, FileText } from 'lucide-react';
import { STATE_LABELS, STATE_BADGE_CLASSES } from '@/lib/constants/states';

interface KanbanCardProps {
  id: string;
  refId: string;
  client: string;
  status: string;
  amount: number;
  currency: string;
  daysInStatus: number;
  onClick?: () => void;
}

export function KanbanCard({ refId, client, status, amount, currency, daysInStatus, onClick }: KanbanCardProps) {
  const isStalled = daysInStatus > 3;

  return (
    <div 
      onClick={onClick}
      className="p-4 rounded-xl cursor-pointer transition-all hover:shadow-md"
      style={{ 
        background: "var(--surface)", 
        border: `1px solid ${isStalled ? 'var(--warning)' : 'var(--border)'}`,
        boxShadow: "var(--shadow-sm)"
      }}
    >
      <div className="flex justify-between items-start mb-3">
        <span className="font-mono text-sm font-medium" style={{ color: "var(--text-secondary)" }}>{refId}</span>
        <span className={`badge ${STATE_BADGE_CLASSES[status] || 'badge-info'}`}>
          {STATE_LABELS[status as keyof typeof STATE_LABELS] || status}
        </span>
      </div>
      
      <h3 className="font-medium mb-1 truncate" style={{ color: "var(--text-primary)" }}>{client}</h3>
      <p className="text-lg font-semibold tracking-tight mb-4" style={{ color: "var(--text-primary)" }}>
        {amount.toLocaleString()} {currency}
      </p>

      <div className="flex items-center justify-between text-xs pt-3" style={{ borderTop: "1px solid var(--divider)", color: "var(--text-tertiary)" }}>
        <div className="flex items-center gap-1" style={{ color: isStalled ? 'var(--warning-dark, var(--warning))' : 'inherit' }}>
          {isStalled ? <AlertTriangle size={14} /> : <Clock size={14} />}
          <span className={isStalled ? "font-medium" : ""}>{daysInStatus} días en estado</span>
        </div>
        <div className="flex items-center gap-1">
          <FileText size={14} />
          <span>Ver det.</span>
        </div>
      </div>
    </div>
  );
}
