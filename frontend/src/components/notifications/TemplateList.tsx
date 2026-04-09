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
      <div className="bg-navy overflow-hidden p-8 text-center text-[rgba(255,255,255,0.5)]">
        No hay templates configurados.
      </div>
    );
  }

  return (
    <div className="bg-navy overflow-hidden">
      <table className="w-full text-sm text-left text-[rgba(255,255,255,0.8)]">
        <thead className="text-xs uppercase bg-navy-dark text-[rgba(255,255,255,0.6)] border-b border-[rgba(255,255,255,0.1)]">
          <tr>
            <th className="px-6 py-4 font-semibold">Key / Título</th>
            <th className="px-6 py-4 font-semibold">Brand / Idioma</th>
            <th className="px-6 py-4 font-semibold">Subject Preview</th>
            <th className="px-6 py-4 font-semibold">Status</th>
            <th className="px-6 py-4 font-semibold text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[rgba(255,255,255,0.06)]">
          {templates.map((tpl) => (
            <tr key={tpl.id} className={`hover:bg-[rgba(255,255,255,0.02)] transition-colors ${!tpl.is_active ? 'opacity-50' : ''}`}>
              <td className="px-6 py-4">
                <div className="font-medium text-white">{tpl.template_key}</div>
                <div className="text-xs text-[rgba(255,255,255,0.5)] mt-1">{tpl.name}</div>
              </td>
              <td className="px-6 py-4">
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-[rgba(255,255,255,0.1)] text-white mr-2">
                  {tpl.brand_name}
                </span>
                <span className="uppercase text-xs font-bold text-mint">{tpl.language}</span>
              </td>
              <td className="px-6 py-4 truncate max-w-xs" title={tpl.subject_template}>
                {tpl.subject_template}
              </td>
              <td className="px-6 py-4">
                <span className={`px-2 py-1 text-[10px] font-bold uppercase rounded-full ${tpl.is_active ? 'bg-[rgba(117,203,179,0.15)] text-mint' : 'bg-red-500/20 text-red-400'}`}>
                  {tpl.is_active ? "Activo" : "Inactivo"}
                </span>
              </td>
              <td className="px-6 py-4 text-right">
                <button 
                  onClick={() => onToggleStatus(tpl.id, tpl.is_active)}
                  className="text-xs text-mint hover:text-white transition-colors"
                >
                  {tpl.is_active ? "Desactivar" : "Reactivar"}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
