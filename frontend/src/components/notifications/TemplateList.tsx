"use client";

import { format } from "date-fns";

type Template = {
  id: string;
  name: string;
  template_key: string;
  subject_template: string;
  is_active: boolean;
  brand_name: string;
  language: string;
  created_at: string;
};

interface Props {
  templates: Template[];
  onToggleStatus: (id: string, currentStatus: boolean) => void;
}

export function TemplateList({ templates, onToggleStatus }: Props) {
  if (templates.length === 0) {
    return (
      <div className="bg-surface rounded-xl shadow-sm border border-border p-8 text-center text-text-tertiary">
        No hay templates configurados.
      </div>
    );
  }

  return (
    <div className="bg-surface rounded-xl shadow-sm border border-border overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse whitespace-nowrap">
          <thead>
            <tr className="bg-bg-alt/50 text-xs uppercase text-text-tertiary font-semibold tracking-wider border-b border-border">
            <th className="px-5 py-4">Key / Título</th>
            <th className="px-5 py-4">Brand / Idioma</th>
            <th className="px-5 py-4">Subject Preview</th>
            <th className="px-5 py-4">Status</th>
            <th className="px-5 py-4 text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {templates.map((tpl) => (
            <tr key={tpl.id} className={`group border-b border-divider hover:bg-surface-hover transition-colors ${!tpl.is_active ? 'opacity-50 bg-bg-alt/30' : 'bg-surface'}`}>
              <td className="px-5 py-4">
                <div className="text-sm font-medium text-text-primary group-hover:text-mint transition-colors">{tpl.template_key}</div>
                <div className="text-xs text-text-tertiary mt-1">{tpl.name}</div>
              </td>
              <td className="px-5 py-4">
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-bg text-text-secondary border border-border mr-2">
                  {tpl.brand_name}
                </span>
                <span className="uppercase text-xs font-bold text-mint">{tpl.language}</span>
              </td>
              <td className="px-5 py-4 truncate max-w-xs text-text-secondary" title={tpl.subject_template}>
                {tpl.subject_template}
              </td>
              <td className="px-5 py-4">
                <span className={`px-2.5 py-1 text-[11px] font-semibold uppercase rounded-md border ${tpl.is_active ? 'bg-mint-soft/10 text-mint border-current' : 'bg-coral-soft/10 text-coral border-current'}`}>
                  {tpl.is_active ? "Activo" : "Inactivo"}
                </span>
              </td>
              <td className="px-5 py-4 text-right">
                <button 
                  onClick={() => onToggleStatus(tpl.id, tpl.is_active)}
                  className="text-xs text-mint hover:text-mint-hover transition-colors font-medium border border-mint/30 hover:border-mint px-3 py-1.5 rounded-lg"
                >
                  {tpl.is_active ? "Desactivar" : "Reactivar"}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
    </div>
  );
}
