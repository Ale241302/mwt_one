import React from 'react';
import { AlertCircle, Clock, ArrowRight } from 'lucide-react';

interface UrgentAction {
  id: string;
  ref: string;
  client: string;
  status: string;
  priority: 'high' | 'critical';
  dueDate: string;
  actionRequired: string; // The 7 fields mapping
}

interface UrgentActionsProps {
  actions?: UrgentAction[];
}

export function UrgentActions({ actions = [] }: UrgentActionsProps) {
  if (!actions || actions.length === 0) {
    return (
      <div className="card p-8 flex flex-col items-center justify-center text-center" style={{ color: "var(--text-secondary)" }}>
        <AlertCircle size={48} className="mb-4 opacity-50" />
        <h3 className="text-lg font-medium" style={{ color: "var(--text-primary)" }}>No hay acciones urgentes</h3>
        <p className="text-sm mt-1">Todos los procesos están al día.</p>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="p-4 flex justify-between items-center" style={{ borderBottom: "1px solid var(--divider)" }}>
        <h2 className="heading-md flex items-center gap-2" style={{ color: "var(--critical)" }}>
          <AlertCircle size={18} /> Acciones Urgentes ({actions.length})
        </h2>
      </div>
      <div>
        {actions.map((action, index) => (
          <div key={action.id} className="p-4 flex items-start justify-between gap-4 transition-colors hover:bg-gray-50" style={{ borderBottom: index < actions.length - 1 ? "1px solid var(--divider)" : "none" }}>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="font-mono text-sm font-medium">{action.ref}</span>
                <span className={`badge ${action.priority === 'critical' ? 'badge-critical' : 'badge-warning'}`}>
                  {action.priority === 'critical' ? 'Crítico' : 'Alto'}
                </span>
              </div>
              <p className="font-medium mb-1" style={{ color: "var(--text-primary)" }}>{action.actionRequired}</p>
              <div className="flex gap-4 text-sm" style={{ color: "var(--text-secondary)" }}>
                <span>{action.client}</span>
                <span className="flex items-center gap-1"><Clock size={14} /> Vence: {action.dueDate}</span>
                <span>Estado: {action.status}</span>
              </div>
            </div>
            <button className="btn btn-sm btn-ghost p-2 rounded-full" style={{ color: "var(--critical)" }}>
              <ArrowRight size={18} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
