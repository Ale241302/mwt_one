"use client";

import { useState, useEffect } from "react";
import { format } from "date-fns";
import api from "@/lib/api";

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

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const res = await api.get("/api/notifications/templates/");
      setTemplates(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const toggleStatus = async (id: string, currentStatus: boolean) => {
    try {
      if (currentStatus) {
        await api.delete(`/api/notifications/templates/${id}/`);
      } else {
        await api.post(`/api/notifications/templates/${id}/restore/`);
      }
      fetchTemplates();
    } catch (err) {
      console.error(err);
      alert("Error cambiando estado");
    }
  };

  if (loading) return <div className="p-8 text-white">Cargando templates...</div>;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Email Templates</h1>
          <p className="text-[rgba(255,255,255,0.6)] mt-2">
            Plantillas para notificaciones automáticas y transaccionales (CEO only).
          </p>
        </div>
      </div>

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
                    onClick={() => toggleStatus(tpl.id, tpl.is_active)}
                    className="text-xs text-mint hover:text-white transition-colors"
                  >
                    {tpl.is_active ? "Desactivar" : "Reactivar"}
                  </button>
                </td>
              </tr>
            ))}
            {templates.length === 0 && (
              <tr>
                <td colSpan={5} className="px-6 py-8 text-center text-[rgba(255,255,255,0.5)]">
                  No hay templates configurados.
                </td>
              </tr>
            )}
           </tbody>
        </table>
      </div>
    </div>
  );
}
