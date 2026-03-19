"use client";

import { useState, useEffect, useCallback } from "react";
import { ArrowLeft, FileText } from "lucide-react";
import Link from "next/link";
import api from "@/lib/api";
import { useParams } from "next/navigation";
import { StateBadge } from "@/components/ui/StateBadge";
import { cn } from "@/lib/utils";

interface Artifact {
  artifact_id: string;
  artifact_type: string;
  status: string;
  created_at: string;
}

interface Expediente {
  expediente_id: string;
  status: string;
  created_at: string;
  updated_at: string;
  brand_name: string;
}

export default function PortalExpedienteDetail() {
  const params = useParams();
  const lang = (params?.lang as string) || "es";
  const expedienteId = params?.id as string;
  
  const [expediente, setExpediente] = useState<Expediente | null>(null);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [expRes, artRes] = await Promise.all([
        api.get(`/portal/expedientes/${expedienteId}/`),
        api.get(`/portal/expedientes/${expedienteId}/artifacts/`), // Wait, did I create this? No.
      ]);
      setExpediente(expRes.data);
      setArtifacts(artRes.data || []);
    } catch (err) {
      console.error("Error fetching expediente detail:", err);
    } finally {
      setLoading(false);
    }
  }, [expedienteId]);

  useEffect(() => {
    if (expedienteId) fetchData();
  }, [expedienteId, fetchData]);

  if (loading) return <div className="empty-state">Cargando...</div>;
  if (!expediente) return <div className="empty-state">Expediente no encontrado.</div>;

  const basePath = `/${lang}/dashboard/portal`;

  return (
    <div className="max-w-4xl mx-auto py-6">
      <Link href={basePath} className="btn btn-ghost btn-sm mb-6">
        <ArrowLeft size={16} className="mr-2" /> Volver al portal
      </Link>

      <div className="card mb-8">
        <div className="flex flex-wrap items-center justify-between gap-4 p-6">
          <div>
            <h1 className="body-lg font-bold mono" style={{ color: "var(--text-primary)" }}>
              EXPEDIENTE {expediente.expediente_id.substring(0, 8).toUpperCase()}
            </h1>
            <p className="body-sm text-secondary">
              Iniciado el {new Date(expediente.created_at).toLocaleDateString()}
            </p>
          </div>
          <StateBadge state={expediente.status as any} />
        </div>
      </div>

      <h2 className="body-lg font-bold mb-4">Documentación y Estado</h2>
      
      <div className="grid gap-4">
        {artifacts.length === 0 ? (
          <div className="card p-8 text-center text-secondary">
            No hay artefactos registrados para este expediente.
          </div>
        ) : (
          artifacts.map((art) => (
            <div key={art.artifact_id} className="card p-4 flex items-center justify-between hover:bg-surface-hover transition-colors">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                  <FileText size={20} />
                </div>
                <div>
                  <p className="body-sm font-bold">{art.artifact_type}</p>
                  <p className="body-xs text-secondary">
                    Actualizado el {new Date(art.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className={cn(
                  "badge",
                  art.status === "APPROVED" ? "badge-success" : 
                  art.status === "DRAFT" ? "badge-warning" : "badge-neutral"
                )}>
                  {art.status}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
