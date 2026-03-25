"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Truck, Plus, Search, ChevronRight } from "lucide-react";
import api from "@/lib/api";
import FormModal from "@/components/ui/FormModal";

interface Supplier {
  id: number;
  name: string;
  tax_id: string;
  country: string;
  is_active: boolean;
  active_agreements_count: number;
  latest_rating: number | null;
  primary_contact?: {
    name: string;
    email: string;
  };
}

interface Brand {
  id: number;
  name: string;
}

const emptyForm = {
  name: "",
  tax_id: "",
  country: "",
  address: "",
  website: "",
  is_active: true,
};

export default function SuppliersPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const lang = (params?.lang as string) || "es";

  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [brands, setBrands] = useState<Brand[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [search, setSearch] = useState(searchParams.get("search") || "");
  const [country, setCountry] = useState(searchParams.get("country") || "");
  const [brand, setBrand] = useState(searchParams.get("brand") || "");

  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSuppliers = useCallback(async () => {
    setLoading(true);
    try {
      const query = new URLSearchParams();
      if (search) query.set("search", search);
      if (country) query.set("country", country);
      if (brand) query.set("brand", brand);

      const [sr, br] = await Promise.all([
        api.get(`/suppliers/?${query.toString()}`),
        api.get("/brands/").catch(() => ({ data: [] })),
      ]);
      setSuppliers(sr.data?.results || sr.data || []);
      setBrands(br.data?.results || br.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [search, country, brand]);

  useEffect(() => {
    fetchSuppliers();
  }, [fetchSuppliers]);

  const updateFilters = (newFilters: Record<string, string>) => {
    const nextParams = new URLSearchParams(searchParams.toString());
    Object.entries(newFilters).forEach(([key, value]) => {
      if (value) nextParams.set(key, value);
      else nextParams.delete(key);
    });
    router.push(`/${lang}/suppliers?${nextParams.toString()}`);
  };

  const openCreate = () => { setForm(emptyForm); setError(null); setShowForm(true); };
  
  const handleSave = async () => {
    if (!form.name.trim() || !form.tax_id.trim()) return;
    
    // Simple URL validation if provided
    if (form.website && !form.website.match(/^https?:\/\/.+/)) {
      setError("El sitio web debe comenzar con http:// o https://");
      return;
    }

    setSaving(true);
    setError(null);
    try {
      await api.post("/suppliers/", form);
      setShowForm(false);
      await fetchSuppliers();
    } catch (err: any) {
      console.error(err);
      const msg = err.response?.data ? JSON.stringify(err.response.data) : "Error al crear el proveedor.";
      setError(msg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Proveedores</h1>
          <p className="page-subtitle">Gestión de cadena de suministro y acuerdos.</p>
        </div>
        <button className="btn btn-md btn-primary" onClick={openCreate}>
          <Plus size={18} /> Nuevo proveedor
        </button>
      </div>

      <div className="flex flex-col md:flex-row gap-4 mb-6 items-end">
        <div className="flex-1 min-w-[200px]">
          <label className="th-label mb-1 block">Búsqueda</label>
          <div className="relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-tertiary" />
            <input
              type="text"
              placeholder="Nombre o Tax ID..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onBlur={() => updateFilters({ search })}
              onKeyDown={(e) => e.key === 'Enter' && updateFilters({ search })}
              className="input pl-10"
            />
          </div>
        </div>
        
        <div className="w-full md:w-48">
          <label className="th-label mb-1 block">País</label>
          <input
            type="text"
            placeholder="Filtrar país..."
            value={country}
            onChange={(e) => setCountry(e.target.value)}
            onBlur={() => updateFilters({ country })}
            onKeyDown={(e) => e.key === 'Enter' && updateFilters({ country })}
            className="input"
          />
        </div>

        <div className="w-full md:w-48">
          <label className="th-label mb-1 block">Marca</label>
          <select 
            className="input" 
            value={brand} 
            onChange={(e) => {
              const val = e.target.value;
              setBrand(val);
              updateFilters({ brand: val });
            }}
          >
            <option value="">Todas las marcas</option>
            {brands.map(b => (
              <option key={b.id} value={b.id}>{b.name}</option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="empty-state"><p>Cargando proveedores...</p></div>
      ) : suppliers.length === 0 ? (
        <div className="empty-state">
          <Truck size={40} className="mb-2 text-tertiary" />
          <p>No se encontraron proveedores.</p>
        </div>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Proveedor</th>
                <th>País</th>
                <th>Contacto Principal</th>
                <th style={{ textAlign: "center" }}>Acuerdos Activos</th>
                <th style={{ textAlign: "center" }}>OTIF</th>
                <th>Estado</th>
                <th style={{ width: 80 }}></th>
              </tr>
            </thead>
            <tbody>
              {suppliers.map((s) => (
                <tr key={s.id} className="group cursor-pointer hover:bg-surface-secondary" onClick={() => router.push(`/${lang}/suppliers/${s.id}`)}>
                  <td>
                    <div className="font-semibold text-primary">{s.name}</div>
                    <div className="text-xs text-tertiary">{s.tax_id}</div>
                  </td>
                  <td>{s.country}</td>
                  <td>
                    {s.primary_contact ? (
                      <div>
                        <div className="text-sm">{s.primary_contact.name}</div>
                        <div className="text-xs text-tertiary">{s.primary_contact.email}</div>
                      </div>
                    ) : (
                      <span className="text-tertiary text-xs">— Sin asignar —</span>
                    )}
                  </td>
                  <td className="text-center">
                    <span className="badge badge-outline">{s.active_agreements_count}</span>
                  </td>
                  <td className="text-center font-mono">
                    {s.latest_rating !== null ? `${s.latest_rating}%` : "—"}
                  </td>
                  <td>
                    <span className={`badge ${s.is_active ? "badge-success" : "badge-outline"}`}>
                      {s.is_active ? "Activo" : "Inactivo"}
                    </span>
                  </td>
                  <td>
                    <button className="btn btn-sm btn-ghost ml-auto">
                      <ChevronRight size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <FormModal
        open={showForm}
        onClose={() => setShowForm(false)}
        title="Nuevo Proveedor"
        footer={
          <div className="flex justify-end gap-2">
            <button className="btn btn-md btn-secondary" onClick={() => setShowForm(false)}>Cancelar</button>
            <button 
              className="btn btn-md btn-primary" 
              onClick={handleSave}
              disabled={saving || !form.name || !form.tax_id}
            >
              {saving ? "Guardando..." : "Crear Proveedor"}
            </button>
          </div>
        }
      >
        <div className="space-y-4">
          {error && (
            <div className="p-3 bg-red-50 text-red-600 border border-red-200 rounded text-sm mb-4 animate-in fade-in">
              <strong>Error:</strong> {error}
            </div>
          )}
          <div>
            <label className="th-label mb-1 block">Nombre Comercial</label>
            <input 
              className="input" 
              value={form.name} 
              onChange={e => setForm({...form, name: e.target.value})}
              placeholder="Ej: ABC Logistics"
            />
          </div>
          <div>
            <label className="th-label mb-1 block">Tax ID / RUC / NIT</label>
            <input 
              className="input" 
              value={form.tax_id} 
              onChange={e => setForm({...form, tax_id: e.target.value})}
              placeholder="ID legal único"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="th-label mb-1 block">País</label>
              <input 
                className="input" 
                value={form.country} 
                onChange={e => setForm({...form, country: e.target.value})}
                placeholder="Costa Rica"
              />
            </div>
            <div>
              <label className="th-label mb-1 block">Sitio Web</label>
              <input 
                className="input" 
                value={form.website} 
                onChange={e => setForm({...form, website: e.target.value})}
                placeholder="https://www.example.com"
              />
            </div>
          </div>
        </div>
      </FormModal>
    </div>
  );
}
