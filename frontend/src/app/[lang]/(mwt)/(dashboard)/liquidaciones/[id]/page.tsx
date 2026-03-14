"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Upload, FileSpreadsheet, CheckCircle, XCircle, AlertTriangle, CheckSquare } from "lucide-react";
import { cn } from "@/lib/utils";

// ─── Types ────────────────────────────────────────────────────────────────────
interface LineaLiquidacion {
  id: string;
  expediente_ref: string;
  concepto: string;
  monto_marluvas: number;
  monto_mwt: number;
  diferencia: number;
  estado: "MATCH" | "DISCREPANCIA" | "APROBADA" | "SOLO_MARLUVAS" | "SOLO_MWT";
}

interface LiquidacionDetalle {
  id: string;
  periodo: string;
  estado: string;
  monto_total: number;
  moneda: string;
  lineas: LineaLiquidacion[];
}

// ─── Upload zone ──────────────────────────────────────────────────────────────
function UploadZone({ onFile }: { onFile: (f: File) => void }) {
  const [dragOver, setDragOver] = useState(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) onFile(file);
  };

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
      className={cn(
        "border-2 border-dashed rounded-xl p-12 text-center transition-colors cursor-pointer",
        dragOver ? "border-mint bg-[#F0FAF6]" : "border-border hover:border-mint hover:bg-bg"
      )}
    >
      <FileSpreadsheet size={40} className="mx-auto text-text-secondary opacity-60 mb-3" />
      <p className="font-medium text-navy mb-1">Arrastrá el Excel Marluvas aquí</p>
      <p className="text-xs text-text-secondary mb-4">O hacé clic para seleccionar un archivo .xlsx</p>
      <label className="inline-flex items-center gap-2 px-4 py-2 bg-navy text-white rounded-lg text-sm font-medium cursor-pointer hover:bg-navy-dark transition-colors">
        <Upload size={14} />
        Seleccionar archivo
        <input
          type="file"
          accept=".xlsx,.xls"
          className="hidden"
          onChange={(e) => { const f = e.target.files?.[0]; if (f) onFile(f); }}
        />
      </label>
    </div>
  );
}

// ─── Línea row ────────────────────────────────────────────────────────────────
function LineaRow({ linea, onAprobar }: { linea: LineaLiquidacion; onAprobar: (id: string) => void }) {
  const isDiscrepancia = linea.estado === "DISCREPANCIA";
  const isMatch = linea.estado === "MATCH" || linea.estado === "APROBADA";

  return (
    <tr className={cn("text-sm transition-colors", isDiscrepancia ? "bg-[#FEF2F2]" : isMatch ? "bg-[#F0FAF6]" : "hover:bg-bg")}>
      <td className="px-4 py-3 font-mono text-xs font-medium text-navy">{linea.expediente_ref}</td>
      <td className="px-4 py-3 text-text-secondary">{linea.concepto}</td>
      <td className={cn("px-4 py-3 font-mono text-right", isMatch ? "text-[#0E8A6D]" : "text-text")}>
        {Number(linea.monto_marluvas).toLocaleString("es-CO", { minimumFractionDigits: 2 })}
      </td>
      <td className={cn("px-4 py-3 font-mono text-right", isMatch ? "text-[#0E8A6D]" : "text-text")}>
        {Number(linea.monto_mwt).toLocaleString("es-CO", { minimumFractionDigits: 2 })}
      </td>
      <td className={cn("px-4 py-3 font-mono text-right font-semibold", isDiscrepancia ? "text-[#DC2626]" : "text-[#0E8A6D]")}>
        {linea.diferencia !== 0 ? (linea.diferencia > 0 ? "+" : "") + Number(linea.diferencia).toLocaleString("es-CO", { minimumFractionDigits: 2 }) : "—"}
      </td>
      <td className="px-4 py-3 text-center">
        {linea.estado === "APROBADA" ? (
          <CheckCircle size={16} className="mx-auto text-[#0E8A6D]" />
        ) : isDiscrepancia ? (
          <XCircle size={16} className="mx-auto text-[#DC2626]" />
        ) : isMatch ? (
          <button
            onClick={() => onAprobar(linea.id)}
            className="text-xs font-semibold text-[#0E8A6D] hover:underline"
          >
            Aprobar
          </button>
        ) : (
          <AlertTriangle size={16} className="mx-auto text-[#B45309]" />
        )}
      </td>
    </tr>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────
export default function LiquidacionDetallePage() {
  const { id } = useParams() as { id: string };
  const router = useRouter();
  const [liq, setLiq] = useState<LiquidacionDetalle | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState<{ type: "ok" | "error"; text: string } | null>(null);

  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : "";
  const BASE = process.env.NEXT_PUBLIC_API_URL;

  const fetchLiq = useCallback(async () => {
    try {
      const res = await fetch(`${BASE}/api/liquidaciones/${id}/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`Error ${res.status}`);
      setLiq(await res.json());
    } catch {
      setLiq(null);
    } finally {
      setLoading(false);
    }
  }, [id, token, BASE]);

  useEffect(() => { fetchLiq(); }, [fetchLiq]);

  async function handleUpload(file: File) {
    setUploading(true);
    setUploadMsg(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(`${BASE}/api/liquidaciones/${id}/upload/`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      if (!res.ok) throw new Error(`Error ${res.status}`);
      setUploadMsg({ type: "ok", text: "Excel procesado correctamente. Revisá las líneas abajo." });
      await fetchLiq();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Error";
      setUploadMsg({ type: "error", text: `No se pudo procesar el archivo. ${msg}` });
    } finally {
      setUploading(false);
    }
  }

  async function aprobarLinea(lineaId: string) {
    try {
      await fetch(`${BASE}/api/liquidaciones/${id}/lineas/${lineaId}/aprobar/`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      await fetchLiq();
    } catch { /* silent */ }
  }

  async function aprobarTodasCoincidentes() {
    try {
      await fetch(`${BASE}/api/liquidaciones/${id}/aprobar-matches/`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      await fetchLiq();
    } catch { /* silent */ }
  }

  const lineas = liq?.lineas ?? [];
  const matches = lineas.filter((l) => l.estado === "MATCH").length;
  const discrepancias = lineas.filter((l) => l.estado === "DISCREPANCIA").length;

  return (
    <div className="space-y-6">
      {/* Back + Header */}
      <div>
        <button onClick={() => router.back()} className="flex items-center gap-1 text-sm text-text-secondary hover:text-navy mb-3">
          <ArrowLeft size={14} /> Volver a liquidaciones
        </button>
        {loading ? (
          <div className="h-8 w-48 bg-bg rounded animate-pulse" />
        ) : (
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-display font-bold text-navy">{liq?.periodo ?? "Liquidación"}</h1>
              <p className="text-sm text-text-secondary mt-0.5">Reconciliación de pagos Marluvas.</p>
            </div>
            {matches > 0 && (
              <button
                onClick={aprobarTodasCoincidentes}
                className="inline-flex items-center gap-2 px-4 py-2 bg-[#0E8A6D] text-white rounded-xl text-sm font-medium hover:opacity-90 transition-opacity"
              >
                <CheckSquare size={16} />
                Aprobar todas coincidentes ({matches})
              </button>
            )}
          </div>
        )}
      </div>

      {/* Upload zone */}
      <div className="bg-white rounded-xl border border-border p-6">
        <h2 className="text-sm font-semibold text-navy mb-4 flex items-center gap-2">
          <Upload size={16} /> Cargar Excel Marluvas
        </h2>
        {uploading ? (
          <div className="p-8 text-center text-text-secondary text-sm">Procesando archivo…</div>
        ) : (
          <UploadZone onFile={handleUpload} />
        )}
        {uploadMsg && (
          <p className={cn("mt-3 text-sm text-center", uploadMsg.type === "ok" ? "text-[#0E8A6D]" : "text-[#DC2626]")}>
            {uploadMsg.text}
          </p>
        )}
      </div>

      {/* Tabla comparativa */}
      {lineas.length > 0 && (
        <div className="bg-white rounded-xl border border-border">
          <div className="px-6 py-4 border-b border-border flex items-center justify-between">
            <h2 className="text-sm font-semibold text-navy">Comparativa línea por línea</h2>
            <div className="flex items-center gap-4 text-xs text-text-secondary">
              <span className="text-[#0E8A6D]">✓ {matches} coincidentes</span>
              {discrepancias > 0 && <span className="text-[#DC2626]">✗ {discrepancias} discrepancias</span>}
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-bg">
                  <th className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-[0.5px] text-text-secondary">Expediente</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-[0.5px] text-text-secondary">Concepto</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold uppercase tracking-[0.5px] text-text-secondary">Marluvas</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold uppercase tracking-[0.5px] text-text-secondary">MWT</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold uppercase tracking-[0.5px] text-text-secondary">Diferencia</th>
                  <th className="text-center px-4 py-3 text-xs font-semibold uppercase tracking-[0.5px] text-text-secondary">Acción</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {lineas.map((l) => (
                  <LineaRow key={l.id} linea={l} onAprobar={aprobarLinea} />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
