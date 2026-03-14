"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Save } from "lucide-react";

export default function NuevaLiquidacionPage() {
  const router = useRouter();
  const [periodo, setPeriodo] = useState("");
  const [moneda, setMoneda] = useState("USD");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/liquidaciones/`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ periodo, moneda }),
      });
      if (!res.ok) throw new Error(`Error ${res.status}`);
      const data = await res.json();
      router.push(`/liquidaciones/${data.id}`);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error al crear liquidación");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-lg space-y-6">
      <div>
        <button onClick={() => router.back()} className="flex items-center gap-1 text-sm text-text-secondary hover:text-navy mb-3">
          <ArrowLeft size={14} /> Volver
        </button>
        <h1 className="text-2xl font-display font-bold text-navy">Nueva liquidación</h1>
        <p className="text-sm text-text-secondary mt-0.5">Reconciliación de pagos Marluvas.</p>
      </div>

      <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-border p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-navy mb-1">Período</label>
          <input
            type="text"
            placeholder="Ej: 2026-02"
            value={periodo}
            onChange={(e) => setPeriodo(e.target.value)}
            required
            className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-mint"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-navy mb-1">Moneda</label>
          <select
            value={moneda}
            onChange={(e) => setMoneda(e.target.value)}
            className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-mint"
          >
            <option value="USD">USD</option>
            <option value="COP">COP</option>
          </select>
        </div>
        {error && <p className="text-sm text-[#DC2626]">{error}</p>}
        <button
          type="submit"
          disabled={loading || !periodo}
          className="inline-flex items-center gap-2 px-4 py-2 bg-navy text-white rounded-xl text-sm font-medium hover:bg-navy-dark disabled:opacity-50 transition-colors"
        >
          <Save size={16} />
          {loading ? "Creando…" : "Crear liquidación"}
        </button>
      </form>
    </div>
  );
}
