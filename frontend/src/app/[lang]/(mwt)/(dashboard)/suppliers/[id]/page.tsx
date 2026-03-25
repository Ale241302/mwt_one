"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { 
  Truck, Building2, FileText, BarChart3, Package, 
  ArrowLeft, Plus, Mail, Phone, Globe, MapPin, 
  ChevronRight, ExternalLink
} from "lucide-react";
import api from "@/lib/api";
import FormModal from "@/components/ui/FormModal";
import { cn } from "@/lib/utils";

export default function SupplierDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id;
  const lang = (params?.lang as string) || "es";
  
  const [supplier, setSupplier] = useState<any>(null);
  const [contacts, setContacts] = useState<any[]>([]);
  const [agreements, setAgreements] = useState<any[]>([]);
  const [catalog, setCatalog] = useState<any>(null);
  const [kpis, setKpis] = useState<any[]>([]);
  
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("identity");
  
  const [showKpiModal, setShowKpiModal] = useState(false);
  const [kpiForm, setKpiForm] = useState({
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1,
    on_time_delivery_score: 100,
    quality_score: 100,
    cost_score: 100,
    comments: ""
  });
  const [savingKpi, setSavingKpi] = useState(false);

  const fetchData = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const [sr, cr, ar, catR, kr] = await Promise.all([
        api.get(`/suppliers/${id}/`),
        api.get(`/suppliers/${id}/contacts/`),
        api.get(`/suppliers/${id}/agreements/`),
        api.get(`/suppliers/${id}/catalog/`),
        api.get(`/suppliers/${id}/performance/`),
      ]);
      setSupplier(sr.data);
      setContacts(cr.data);
      setAgreements(ar.data);
      setCatalog(catR.data);
      setKpis(kr.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleSaveKpi = async () => {
    setSavingKpi(true);
    try {
      await api.post(`/suppliers/${id}/register_kpi/`, kpiForm);
      setShowKpiModal(false);
      await fetchData();
    } catch (err) {
      console.error(err);
      alert("Error al registrar KPI. Es posible que ya exista para ese período.");
    } finally {
      setSavingKpi(false);
    }
  };

  if (loading) return <div className="p-8 text-center"><p className="body-lg">Cargando detalles del proveedor...</p></div>;
  if (!supplier) return <div className="p-8 text-center text-critical">Proveedor no encontrado.</div>;

  return (
    <div className="max-w-6xl mx-auto p-4 sm:p-6 lg:p-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-4 mb-8">
        <button 
          onClick={() => router.push(`/${lang}/suppliers`)}
          className="btn btn-sm btn-ghost self-start"
        >
          <ArrowLeft size={18} className="mr-2" /> Volver
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="page-title mb-0">{supplier.name}</h1>
            <span className={`badge ${supplier.is_active ? "badge-success" : "badge-outline"}`}>
              {supplier.is_active ? "Activo" : "Inactivo"}
            </span>
          </div>
          <p className="text-tertiary text-sm mt-1">Tax ID: {supplier.tax_id} • Registrado el {new Date(supplier.created_at).toLocaleDateString()}</p>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="flex border-b border-surface-tertiary mb-6 overflow-x-auto scroller-hide">
        {[
          { id: "identity", label: "Identidad", icon: <Building2 size={18} /> },
          { id: "agreements", label: "Acuerdos", icon: <FileText size={18} /> },
          { id: "catalog", label: "Catálogo", icon: <Package size={18} /> },
          { id: "performance", label: "Desempeño (KPIs)", icon: <BarChart3 size={18} /> }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "flex items-center gap-2 px-6 py-3 border-b-2 transition-all whitespace-nowrap",
              activeTab === tab.id 
                ? "border-primary text-primary font-semibold" 
                : "border-transparent text-tertiary hover:text-secondary hover:bg-surface-secondary"
            )}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="animate-in fade-in duration-300">
        {activeTab === "identity" && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Info Cards */}
            <div className="md:col-span-2 space-y-6">
              <section className="surface p-6 rounded-xl border border-surface-tertiary">
                <h3 className="heading-sm mb-4">Información General</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <div className="th-label">Razón Social</div>
                    <div className="font-medium">{supplier.name}</div>
                  </div>
                  <div className="space-y-1">
                    <div className="th-label">País</div>
                    <div className="flex items-center gap-2">
                       <MapPin size={14} className="text-tertiary" />
                       {supplier.country}
                    </div>
                  </div>
                  <div className="space-y-1">
                    <div className="th-label">Tax ID / NIT / RFC</div>
                    <div className="font-mono text-sm">{supplier.tax_id}</div>
                  </div>
                  <div className="space-y-1">
                    <div className="th-label">Sitio Web</div>
                    {supplier.website ? (
                      <a href={supplier.website} target="_blank" className="text-primary hover:underline flex items-center gap-1">
                        {supplier.website.replace(/^https?:\/\//, '')} <ExternalLink size={12} />
                      </a>
                    ) : "—"}
                  </div>
                </div>
                <div className="mt-4 pt-4 border-t border-surface-tertiary">
                   <div className="th-label mb-1">Dirección Física</div>
                   <p className="text-sm">{supplier.address || "No especificada"}</p>
                </div>
              </section>

              <section className="surface p-6 rounded-xl border border-surface-tertiary">
                <h3 className="heading-sm mb-4">Contactos Directos</h3>
                {contacts.length === 0 ? (
                  <p className="text-tertiary text-sm italic">Sin contactos registrados.</p>
                ) : (
                  <div className="table-container border-none">
                    <table className="compact">
                      <thead>
                        <tr>
                          <th>Nombre / Rol</th>
                          <th>Email / Tel</th>
                          <th style={{ width: 80 }}>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {contacts.map(c => (
                          <tr key={c.id}>
                            <td>
                              <div className="font-medium">{c.name}</div>
                              <div className="text-xs text-tertiary">{c.role || "—"}</div>
                            </td>
                            <td>
                              <div className="flex items-center gap-2 text-xs">
                                <Mail size={12} className="text-tertiary" /> {c.email}
                              </div>
                              {c.phone && (
                                <div className="flex items-center gap-2 text-xs mt-1">
                                  <Phone size={12} className="text-tertiary" /> {c.phone}
                                </div>
                              )}
                            </td>
                            <td>
                              {c.is_primary && <span className="badge badge-primary text-[10px] py-0 px-1">Principal</span>}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </section>
            </div>

            {/* Terms Sidebar */}
            <div className="space-y-6">
              <section className="surface p-5 rounded-xl border border-surface-tertiary bg-surface-secondary/50">
                <h3 className="heading-sm mb-3 text-xs uppercase tracking-wider text-tertiary">Términos Comerciales</h3>
                <div className="space-y-4">
                  <div className="flex justify-between items-start">
                    <span className="text-sm text-tertiary">Incoterm</span>
                    <span className="badge badge-outline">EXW</span>
                  </div>
                  <div className="flex justify-between items-start">
                    <span className="text-sm text-tertiary">Días pago</span>
                    <span className="font-semibold">60 Net</span>
                  </div>
                  <div className="flex justify-between items-start">
                    <span className="text-sm text-tertiary">Moneda</span>
                    <span className="font-mono text-sm">USD</span>
                  </div>
                </div>
                <div className="mt-6 pt-4 border-t border-surface-tertiary text-[11px] text-tertiary italic">
                   Datos del acuerdo maestro vigente.
                </div>
              </section>
            </div>
          </div>
        )}

        {activeTab === "agreements" && (
          <div className="surface rounded-xl border border-surface-tertiary overflow-hidden">
            {agreements.length === 0 ? (
              <div className="p-12 text-center">
                <FileText size={48} className="mx-auto mb-4 text-tertiary opacity-20" />
                <h3 className="heading-sm text-secondary">Sin acuerdos registrados</h3>
                <p className="text-tertiary max-w-xs mx-auto mt-2">No se han cargado BrandSupplierAgreements para este proveedor aún.</p>
              </div>
            ) : (
              <div className="table-container border-none">
                <table>
                  <thead>
                    <tr>
                      <th>Marca</th>
                      <th>Versión</th>
                      <th>Validez</th>
                      <th>Status</th>
                      <th style={{ width: 60 }}></th>
                    </tr>
                  </thead>
                  <tbody>
                    {agreements.map((a: any) => (
                      <tr key={a.id}>
                        <td><span className="font-semibold">{a.brand_name}</span></td>
                        <td>{a.version}</td>
                        <td className="text-sm font-mono">{a.valid_daterange || "Indefinido"}</td>
                        <td>
                          <span className={`badge ${a.status === 'active' ? "badge-success" : "badge-outline"}`}>
                            {a.status.toUpperCase()}
                          </span>
                        </td>
                        <td>
                           <button className="btn btn-sm btn-ghost"><ChevronRight size={14} /></button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {activeTab === "catalog" && (
          <div className="surface rounded-xl border border-surface-tertiary overflow-hidden">
            {!catalog || catalog.count === 0 ? (
              <div className="p-16 text-center">
                <Package size={48} className="mx-auto mb-4 text-tertiary opacity-20" />
                <h3 className="heading-sm text-secondary">Sin catálogo registrado</h3>
                <p className="text-tertiary mt-2">Contacte al equipo de compras para importar el catálogo maestro.</p>
              </div>
            ) : (
              <div className="table-container border-none">
                {/* Catalog Implementation PENDING if schema grows */}
                <p className="p-8 text-center text-tertiary">Catálogo maestro disponible: {catalog.count} items.</p>
              </div>
            )}
          </div>
        )}

        {activeTab === "performance" && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="heading-sm">Histórico de Performance</h3>
              <button className="btn btn-sm btn-primary" onClick={() => setShowKpiModal(true)}>
                <Plus size={16} className="mr-1" /> Registrar período
              </button>
            </div>
            
            <div className="surface rounded-xl border border-surface-tertiary overflow-hidden">
              {kpis.length === 0 ? (
                <div className="p-16 text-center">
                  <BarChart3 size={48} className="mx-auto mb-4 text-tertiary opacity-20" />
                  <p className="text-tertiary">Sin datos de desempeño aún.</p>
                </div>
              ) : (
                <div className="table-container border-none">
                  <table>
                    <thead>
                      <tr>
                        <th>Período</th>
                        <th style={{ textAlign: "center" }}>OTIF</th>
                        <th style={{ textAlign: "center" }}>Calidad</th>
                        <th style={{ textAlign: "center" }}>Cost Sc.</th>
                        <th style={{ textAlign: "center" }}>Rating Gral.</th>
                        <th>Comentarios</th>
                      </tr>
                    </thead>
                    <tbody>
                      {kpis.map((k, i) => (
                        <tr key={i}>
                          <td><span className="font-medium">{k.year} / {String(k.month).padStart(2, '0')}</span></td>
                          <td className="text-center font-mono slashed-zero">
                             {/* TODO: umbrales pendientes CEO — ref ENT_GOB_KPI */}
                             {k.on_time_delivery_score}%
                          </td>
                          <td className="text-center font-mono">{k.quality_score}%</td>
                          <td className="text-center font-mono">{k.cost_score}</td>
                          <td className="text-center">
                             <div className="flex flex-col items-center">
                               <div className="text-lg font-bold text-primary">{k.overall_rating}</div>
                               <div className="text-[9px] text-tertiary uppercase">puntos</div>
                             </div>
                          </td>
                          <td>
                            <div className="max-w-[200px] truncate text-xs text-tertiary" title={k.comments}>
                              {k.comments || "—"}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Register KPI Modal */}
      <FormModal
        open={showKpiModal}
        onClose={() => setShowKpiModal(false)}
        title="Registrar Desempeño"
        footer={
          <div className="flex justify-end gap-2 text-sm">
            <button className="btn btn-md btn-secondary" onClick={() => setShowKpiModal(false)}>Cancelar</button>
            <button 
              className="btn btn-md btn-primary" 
              onClick={handleSaveKpi}
              disabled={savingKpi}
            >
              {savingKpi ? "Procesando..." : "Guardar Registro"}
            </button>
          </div>
        }
      >
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="th-label mb-1 block">Año</label>
            <input type="number" className="input" value={kpiForm.year} onChange={e => setKpiForm({...kpiForm, year: parseInt(e.target.value)})}/>
          </div>
          <div>
            <label className="th-label mb-1 block">Mes</label>
            <select className="input" value={kpiForm.month} onChange={e => setKpiForm({...kpiForm, month: parseInt(e.target.value)})}>
              {Array.from({length: 12}, (_, i) => (
                <option key={i+1} value={i+1}>{new Date(0, i).toLocaleString('es', {month: 'long'})}</option>
              ))}
            </select>
          </div>
        </div>
        <div className="grid grid-cols-3 gap-3 pt-2">
           <div>
             <label className="th-label mb-1 block">OTIF (%)</label>
             <input type="number" step="0.1" className="input text-center" value={kpiForm.on_time_delivery_score} onChange={e => setKpiForm({...kpiForm, on_time_delivery_score: parseFloat(e.target.value)})}/>
           </div>
           <div>
             <label className="th-label mb-1 block">Calidad (%)</label>
             <input type="number" step="0.1" className="input text-center" value={kpiForm.quality_score} onChange={e => setKpiForm({...kpiForm, quality_score: parseFloat(e.target.value)})}/>
           </div>
           <div>
             <label className="th-label mb-1 block">Costo (0-100)</label>
             <input type="number" step="0.1" className="input text-center" value={kpiForm.cost_score} onChange={e => setKpiForm({...kpiForm, cost_score: parseFloat(e.target.value)})}/>
           </div>
        </div>
        <div>
          <label className="th-label mb-1 block">Comentarios adicionales</label>
          <textarea 
            className="input min-h-[80px]" 
            value={kpiForm.comments} 
            onChange={e => setKpiForm({...kpiForm, comments: e.target.value})}
            placeholder="Observaciones sobre el desempeño en este período..."
          />
        </div>
      </FormModal>
    </div>
  );
}
