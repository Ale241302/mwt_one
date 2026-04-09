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
        <button 
          onClick={() => setShowEditor(true)}
          className="bg-mint text-navy-dark px-4 py-2 font-bold rounded hover:bg-mint-hover"
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
