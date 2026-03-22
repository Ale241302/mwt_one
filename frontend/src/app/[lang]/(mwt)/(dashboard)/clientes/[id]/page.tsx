"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Users, FolderOpen, Mail, Phone, Globe, Building, CreditCard, RefreshCw, ArrowRight } from "lucide-react";
import api from "@/lib/api";
import { cn } from "@/lib/utils";
import { STATE_BADGE_CLASSES } from "@/constants/states";

interface Client {
  id: number;
  name: string;
  contact_name: string | null;
  email: string | null;
  phone: string | null;
  country: string | null;
  legal_entity_name: string | null;
  credit_approved: string | null;
  is_active: boolean;
}

interface Expediente {
  id: string;
  custom_ref: string;
  status: string;
  total_cost: number;
  last_event_at: string;
}

export default function ClientDetailPage() {
  const params = useParams();
  const router = useRouter();
  const lang = (params?.lang as string) || "es";
  const id = params?.id as string;

  const [client, setClient] = useState<Client | null>(null);
  const [expedientes, setExpedientes] = useState<Expediente[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // In this project, the api lib usually prefixes with /api if needed or is configured
      // Looking at other files, they use api.get("/api/clientes/") or api.get("/ui/expedientes/")
      const [clientRes, expRes] = await Promise.all([
        api.get(`/api/clientes/${id}/`),
        api.get(`/api/ui/expedientes/?client=${id}`)
      ]);
      setClient(clientRes.data);
      
      // The useFetch logic often handles the .results transformation, 
      // but here we are using api directly.
      const expData = expRes.data?.results || expRes.data || [];
      setExpedientes(Array.isArray(expData) ? expData : []);
    } catch (err: any) {
      console.error(err);
      setError("Error al cargar el detalle del cliente.");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="flex flex-col items-center gap-3">
          <RefreshCw size={24} className="animate-spin text-brand" />
          <p className="text-text-tertiary text-sm">Cargando cliente...</p>
        </div>
      </div>
    );
  }

  if (error || !client) {
    return (
      <div className="empty-state">
        <Users size={48} className="text-text-tertiary mb-4" />
        <p className="text-lg font-medium text-text-primary mb-2">{error || "Cliente no encontrado."}</p>
        <button className="btn btn-secondary" onClick={() => router.back()}>
          <ArrowLeft size={16} className="mr-2" /> Volver
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <Link href={`/${lang}/clientes`} className="btn btn-sm btn-ghost p-2 mt-1">
            <ArrowLeft size={16} />
          </Link>
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="page-title leading-none">{client.name}</h1>
              <span className={`badge ${client.is_active ? "badge-success" : "badge-outline"}`}>
                {client.is_active ? "Activo" : "Inactivo"}
              </span>
            </div>
            <p className="page-subtitle flex items-center gap-2">
              <Building size={14} />
              {client.legal_entity_name || "Sin entidad legal registrada"}
            </p>
          </div>
        </div>
        
        <div className="flex gap-2">
          {/* Add actions if needed, like edit or delete */}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-6">
          <div className="card p-5">
            <h3 className="text-sm font-semibold text-navy uppercase tracking-wider mb-4 border-b border-border pb-2">
              Información del Cliente
            </h3>
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <Users size={18} className="text-text-tertiary mt-0.5" />
                <div>
                  <p className="text-[10px] uppercase font-bold text-text-tertiary tracking-tight">Contacto Principal</p>
                  <p className="text-sm font-medium text-text-primary">{client.contact_name || "—"}</p>
                </div>
              </div>
              
              <div className="flex items-start gap-3">
                <Mail size={18} className="text-text-tertiary mt-0.5" />
                <div>
                  <p className="text-[10px] uppercase font-bold text-text-tertiary tracking-tight">Correo Electrónico</p>
                  {client.email ? (
                    <a href={`mailto:${client.email}`} className="text-sm font-medium text-brand hover:underline">
                      {client.email}
                    </a>
                  ) : (
                    <p className="text-sm font-medium text-text-primary">—</p>
                  )}
                </div>
              </div>

              <div className="flex items-start gap-3">
                <Phone size={18} className="text-text-tertiary mt-0.5" />
                <div>
                  <p className="text-[10px] uppercase font-bold text-text-tertiary tracking-tight">Teléfono</p>
                  <p className="text-sm font-medium text-text-primary">{client.phone || "—"}</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <Globe size={18} className="text-text-tertiary mt-0.5" />
                <div>
                  <p className="text-[10px] uppercase font-bold text-text-tertiary tracking-tight">País / Región</p>
                  <p className="text-sm font-medium text-text-primary">{client.country || "—"}</p>
                </div>
              </div>

              <div className="pt-4 mt-4 border-t border-dashed border-border">
                <div className="flex items-start gap-3">
                  <CreditCard size={18} className="text-text-tertiary mt-0.5" />
                  <div>
                    <p className="text-[10px] uppercase font-bold text-text-tertiary tracking-tight">Crédito Aprobado</p>
                    <p className="text-sm font-semibold text-navy">{client.credit_approved || "—"}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between px-1">
            <h2 className="heading-sm font-semibold text-navy flex items-center gap-2">
              <FolderOpen size={18} />
              Expedientes Asociados
            </h2>
            <span className="badge badge-secondary">{expedientes.length}</span>
          </div>

          {expedientes.length === 0 ? (
            <div className="card p-12 flex flex-col items-center justify-center text-center bg-bg/20 border-dashed border-2 border-border/50">
              <FolderOpen size={48} className="text-text-tertiary/20 mb-3" />
              <p className="text-text-secondary font-medium">No se encontraron expedientes para este cliente.</p>
              <p className="text-xs text-text-tertiary mt-1">Cuando se creen expedientes asociados a este cliente, aparecerán aquí.</p>
            </div>
          ) : (
            <div className="table-container shadow-sm border border-border/60">
              <table>
                <thead>
                  <tr>
                    <th className="w-1/4">Referencia</th>
                    <th>Estado</th>
                    <th className="text-right">Costo Estimado</th>
                    <th>Última Actividad</th>
                    <th className="w-10"></th>
                  </tr>
                </thead>
                <tbody>
                  {expedientes.map((exp) => (
                    <tr key={exp.id} className="hover:bg-bg/40 transition-colors">
                      <td className="font-mono font-bold text-navy truncate max-w-[120px]">
                        {exp.custom_ref}
                      </td>
                      <td>
                        <span className={cn(
                          "badge text-[10px] font-bold px-2 py-0.5",
                          STATE_BADGE_CLASSES[exp.status] || "badge-outline"
                        )}>
                          {exp.status}
                        </span>
                      </td>
                      <td className="text-right font-medium">
                        ${Number(exp.total_cost || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </td>
                      <td className="text-xs text-text-tertiary">
                        {exp.last_event_at ? new Date(exp.last_event_at).toLocaleDateString(undefined, {
                          year: 'numeric', month: 'short', day: 'numeric'
                        }) : "—"}
                      </td>
                      <td>
                        <Link 
                          href={`/${lang}/expedientes/${exp.id}`} 
                          className="btn btn-xs btn-ghost text-brand"
                          title="Ver detalle del expediente"
                        >
                          <ArrowRight size={14} />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
