"use client";

import { useState, useEffect } from "react";
import api from "@/lib/api";
import { TemplateList } from "@/components/notifications/TemplateList";
import { TemplateEditor } from "@/components/notifications/TemplateEditor";

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
  const [showEditor, setShowEditor] = useState(false);

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const res = await api.get("/notifications/templates/");
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
        await api.delete(`/notifications/templates/${id}/`);
      } else {
        await api.post(`/notifications/templates/${id}/restore/`);
      }
      fetchTemplates();
    } catch (err) {
      console.error(err);
      alert("Error cambiando estado");
    }
  };

  if (loading) return <div className="p-8 text-white">Cargando templates...</div>;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-display font-bold">Email Templates</h1>
          <p className="text-sm text-text-tertiary mt-1">
            Plantillas para notificaciones automáticas y transaccionales (CEO only).
          </p>
        </div>
        <button
          onClick={() => setShowEditor(true)}
          className="bg-navy hover:bg-slate-800 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all shadow-sm active:scale-95 flex items-center gap-2"
        >
          Crear Template
        </button>
      </div>

      <TemplateList templates={templates} onToggleStatus={toggleStatus} />

      {showEditor && (
        <TemplateEditor
          onSaved={() => {
            setShowEditor(false);
            fetchTemplates();
          }}
          onClose={() => setShowEditor(false)}
        />
      )}
    </div>
  );
}
