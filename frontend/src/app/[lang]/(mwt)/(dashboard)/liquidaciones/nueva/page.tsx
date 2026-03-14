/**
 * S9-08/09 — Nueva Liquidación
 * - Drag & drop upload de Excel Marluvas (.xlsx / .xls)
 * - Vista previa de filas parseadas antes de confirmar
 * - POST a /api/liquidaciones/ con archivo y período
 */
"use client";
import { useState, useRef, useCallback, DragEvent } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeft, UploadCloud, FileSpreadsheet, X, AlertCircle,
  CheckCircle, Loader2, ChevronDown, ChevronUp,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ─── Tipos ─────────────────────────────────────────────────────────────────────
interface ParsedRow {
  referencia: string;
  descripcion: string;
  cantidad: number;
  precio_unitario: number;
  total: number;
  moneda: string;
  coincide?: boolean; // match con expediente en sistema
}

const ACCEPTED_TYPES = [
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", // .xlsx
  "application/vnd.ms-excel", // .xls
];

const MAX_BYTES = 10 * 1024 * 1024; // 10 MB

// ─── Zona de drop ───────────────────────────────────────────────────────────────────
function DropZone({
  onFile,
  disabled,
}: {
  onFile: (f: File) => void;
  disabled?: boolean;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const handleDrop = useCallback(
    (e: DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files?.[0];
      if (file) onFile(file);
    },
    [onFile]
  );

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); if (!disabled) setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={disabled ? undefined : handleDrop}
      onClick={() => !disabled && inputRef.current?.click()}
      role="button"
      aria-label="Zona de carga de archivo Excel"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && !disabled && inputRef.current?.click()}
      className={cn(
        "flex flex-col items-center justify-center gap-3",
        "border-2 border-dashed rounded-[var(--radius-xl)] py-12 px-6 transition-all cursor-pointer select-none",
        dragging
          ? "border-[var(--mint)] bg-[#E6F7F3]"
          : "border-[var(--border)] bg-[var(--bg-alt)] hover:border-[var(--navy)] hover:bg-[var(--surface-hover)]",
        disabled && "opacity-50 cursor-not-allowed"
      )}
    >
      <UploadCloud size={36} className={cn("transition-colors", dragging ? "text-[var(--mint)]" : "text-[var(--text-disabled)]")} />
      <div className="text-center">
        <p className="text-sm font-medium text-[var(--text-primary)]">
          Arrastra el archivo Excel de Marluvas aquí
        </p>
        <p className="text-xs text-[var(--text-tertiary)] mt-0.5">
          .xlsx o .xls • máx. 10 MB
        </p>
      </div>
      <span className="text-xs font-semibold text-[var(--navy)] border border-[var(--navy)]/30 rounded-lg px-3 py-1.5 hover:bg-[var(--navy)] hover:text-white transition-colors">
        Seleccionar archivo
      </span>
      <input
        ref={inputRef}
        type="file"
        accept=".xlsx,.xls"
        className="sr-only"
        onChange={(e) => { const f = e.target.files?.[0]; if (f) onFile(f); }}
      />
    </div>
  );
}

// ─── Tabla comparativa ──────────────────────────────────────────────────────────────
function ComparativeTable({ rows }: { rows: ParsedRow[] }) {
  const [expanded, setExpanded] = useState(true);
  const matchCount = rows.filter((r) => r.coincide).length;
  const totalAmount = rows.reduce((acc, r) => acc + (r.total ?? 0), 0);
  const moneda = rows[0]?.moneda ?? "USD";

  return (
    <div className="rounded-[var(--radius-xl)] border border-[var(--border)] overflow-hidden">
      {/* Sub-header */}
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center justify-between px-5 py-3 bg-[var(--bg-alt)] hover:bg-[var(--surface-hover)] transition-colors text-left"
      >
        <div className="flex items-center gap-3">
          <FileSpreadsheet size={16} className="text-[var(--navy)]" />
          <span className="text-sm font-semibold text-[var(--text-primary)]">
            {rows.length} filas importadas
          </span>
          <span className="text-xs text-[var(--text-tertiary)]">•</span>
          <span className="text-xs font-medium text-[#0E8A6D)]">
            {matchCount} coincidencias en sistema
          </span>
          <span className="text-xs text-[var(--text-tertiary)]">•</span>
          <span className="text-xs font-mono font-semibold text-[var(--text-primary)]">
            {moneda} {totalAmount.toLocaleString("es-CO", { minimumFractionDigits: 2 })}
          </span>
        </div>
        {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      {expanded && (
        <div className="overflow-x-auto max-h-72 overflow-y-auto">
          <table className="w-full text-xs border-collapse">
            <thead className="sticky top-0 z-10">
              <tr className="bg-[var(--bg)] border-b border-[var(--border)]">
                {["Referencia", "Descripción", "Qty", "Precio Unit.", "Total", "Moneda", "Sistema"].map((h) => (
                  <th key={h} className="px-4 py-2.5 text-left font-semibold uppercase tracking-[0.5px] text-[var(--text-tertiary)] whitespace-nowrap">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--divider)]">
              {rows.map((row, i) => (
                <tr
                  key={i}
                  className={cn(
                    "transition-colors",
                    row.coincide === true
                      ? "bg-[#F0FAF6] hover:bg-[#E6F7F3]"
                      : row.coincide === false
                      ? "bg-[#FEF2F2]/50 hover:bg-[#FEF2F2]"
                      : "hover:bg-[var(--surface-hover)]"
                  )}
                >
                  <td className="px-4 py-2 font-mono font-semibold text-[var(--navy)]">{row.referencia}</td>
                  <td className="px-4 py-2 text-[var(--text-secondary)] max-w-[200px] truncate">{row.descripcion}</td>
                  <td className="px-4 py-2 text-right tabular-nums">{row.cantidad}</td>
                  <td className="px-4 py-2 text-right tabular-nums">
                    {Number(row.precio_unitario).toLocaleString("es-CO", { minimumFractionDigits: 2 })}
                  </td>
                  <td className="px-4 py-2 text-right tabular-nums font-medium">
                    {Number(row.total).toLocaleString("es-CO", { minimumFractionDigits: 2 })}
                  </td>
                  <td className="px-4 py-2 text-[var(--text-secondary)]">{row.moneda}</td>
                  <td className="px-4 py-2">
                    {row.coincide === true && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-[#0E8A6D] bg-[#F0FAF6] px-1.5 py-0.5 rounded-md">
                        <CheckCircle size={10} /> Sí
                      </span>
                    )}
                    {row.coincide === false && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-[#DC2626] bg-[#FEF2F2] px-1.5 py-0.5 rounded-md">
                        <AlertCircle size={10} /> No encontrado
                      </span>
                    )}
                    {row.coincide === undefined && (
                      <span className="text-[10px] text-[var(--text-disabled)]">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ─── Página principal ───────────────────────────────────────────────────────────────────
export default function NuevaLiquidacionPage() {
  const router = useRouter();
  const [periodo, setPeriodo] = useState("");
  const [moneda, setMoneda] = useState("USD");
  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [previewRows, setPreviewRows] = useState<ParsedRow[] | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Validar y cargar archivo → pedir preview al servidor
  async function handleFile(f: File) {
    setFileError(null);
    setPreviewRows(null);
    if (!ACCEPTED_TYPES.includes(f.type) && !f.name.match(/\.(xlsx|xls)$/i)) {
      setFileError("Solo se aceptan archivos .xlsx o .xls");
      return;
    }
    if (f.size > MAX_BYTES) {
      setFileError("El archivo supera el límite de 10 MB");
      return;
    }
    setFile(f);
    setLoadingPreview(true);
    try {
      const token = localStorage.getItem("access_token");
      const fd = new FormData();
      fd.append("file", f);
      // S9-P01: endpoint provisional — verificar URL con CEO
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/liquidaciones/preview/`,
        { method: "POST", headers: { Authorization: `Bearer ${token}` }, body: fd }
      );
      if (res.ok) {
        const data = await res.json();
        setPreviewRows(data.rows ?? []);
      } else {
        // Si el endpoint no existe aún, mostrar placeholder
        setPreviewRows([]);
      }
    } catch {
      setPreviewRows([]);
    } finally {
      setLoadingPreview(false);
    }
  }

  function removeFile() {
    setFile(null);
    setPreviewRows(null);
    setFileError(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!periodo) return;
    setSubmitting(true);
    setError(null);
    try {
      const token = localStorage.getItem("access_token");
      const fd = new FormData();
      fd.append("periodo", periodo);
      fd.append("moneda", moneda);
      if (file) fd.append("archivo_excel", file);
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/liquidaciones/`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: fd,
      });
      if (!res.ok) throw new Error(`Error ${res.status}`);
      const data = await res.json();
      router.push(`/liquidaciones/${data.id}`);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error al crear liquidación");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-2xl space-y-6">
      {/* Back */}
      <div>
        <button
          onClick={() => router.back()}
          className="flex items-center gap-1 text-sm text-[var(--text-secondary)] hover:text-[var(--navy)] mb-3 transition-colors"
        >
          <ArrowLeft size={14} /> Volver
        </button>
        <h1 className="text-2xl font-display font-bold text-[var(--navy)]">Nueva liquidación</h1>
        <p className="text-sm text-[var(--text-secondary)] mt-0.5">Reconciliación de pagos Marluvas.</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Campos básicos */}
        <div className="bg-[var(--surface)] rounded-[var(--radius-xl)] border border-[var(--border)] p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-[var(--navy)] mb-1">
                Período <span className="text-[var(--coral)]">*</span>
              </label>
              <input
                type="text"
                placeholder="Ej: 2026-03"
                value={periodo}
                onChange={(e) => setPeriodo(e.target.value)}
                required
                pattern="\d{4}-\d{2}"
                title="Formato: YYYY-MM"
                className="w-full border border-[var(--border)] rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--mint)] bg-[var(--surface)] text-[var(--text-primary)]"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[var(--navy)] mb-1">Moneda</label>
              <select
                value={moneda}
                onChange={(e) => setMoneda(e.target.value)}
                className="w-full border border-[var(--border)] rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--mint)] bg-[var(--surface)] text-[var(--text-primary)]"
              >
                <option value="USD">USD</option>
                <option value="COP">COP</option>
                <option value="EUR">EUR</option>
              </select>
            </div>
          </div>
        </div>

        {/* Drop zone */}
        {!file ? (
          <DropZone onFile={handleFile} />
        ) : (
          <div className="flex items-center gap-3 bg-[var(--surface)] border border-[var(--border)] rounded-[var(--radius-xl)] px-5 py-3">
            <FileSpreadsheet size={20} className="text-[#0E8A6D] flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-[var(--text-primary)] truncate">{file.name}</p>
              <p className="text-xs text-[var(--text-tertiary)]">
                {(file.size / 1024).toFixed(1)} KB
              </p>
            </div>
            <button
              type="button"
              onClick={removeFile}
              className="p-1.5 rounded-lg hover:bg-[var(--surface-hover)] text-[var(--text-tertiary)] hover:text-[var(--coral)] transition-colors"
              aria-label="Quitar archivo"
            >
              <X size={14} />
            </button>
          </div>
        )}

        {fileError && (
          <p className="flex items-center gap-1.5 text-sm text-[#DC2626]">
            <AlertCircle size={14} /> {fileError}
          </p>
        )}

        {/* Loading preview */}
        {loadingPreview && (
          <div className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
            <Loader2 size={14} className="animate-spin" />
            Analizando archivo…
          </div>
        )}

        {/* Tabla comparativa */}
        {previewRows !== null && previewRows.length > 0 && (
          <ComparativeTable rows={previewRows} />
        )}
        {previewRows !== null && previewRows.length === 0 && file && (
          <p className="text-xs text-[var(--text-tertiary)] text-center py-2">
            El servidor no retornó vista previa — el archivo se subirá al confirmar.
          </p>
        )}

        {/* Error */}
        {error && (
          <div className="flex items-center gap-2 bg-[#FEF2F2] border border-[#DC2626]/20 rounded-lg px-4 py-2.5 text-sm text-[#DC2626]">
            <AlertCircle size={14} className="flex-shrink-0" /> {error}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => router.back()}
            className="px-4 py-2 text-sm font-medium text-[var(--text-secondary)] border border-[var(--border)] rounded-xl hover:bg-[var(--surface-hover)] transition-colors"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={submitting || !periodo}
            className="inline-flex items-center gap-2 px-5 py-2 bg-[var(--navy)] text-white rounded-xl text-sm font-semibold hover:bg-[var(--navy-dark)] disabled:opacity-50 transition-colors"
          >
            {submitting && <Loader2 size={14} className="animate-spin" />}
            {submitting ? "Creando…" : "Crear liquidación"}
          </button>
        </div>
      </form>
    </div>
  );
}
