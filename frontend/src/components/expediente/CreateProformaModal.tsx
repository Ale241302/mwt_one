"use client";

import { useState } from "react";
import { AlertCircle } from "lucide-react";
import api from "@/lib/api";
import FormModal from "@/components/ui/FormModal";
import { BRAND_ALLOWED_MODES, DEFAULT_ALLOWED_MODES } from "@/constants/brand-modes";
import { MODE_LABELS } from "@/constants/mode-labels";

interface CreateProformaModalProps {
  open: boolean;
  expedienteId: string;
  brandSlug: string;
  orphanLines: any[];
  onClose: () => void;
  onRefresh: () => void;
}

export default function CreateProformaModal({
  open, expedienteId, brandSlug, orphanLines, onClose, onRefresh
}: CreateProformaModalProps) {
  // brandSlug could be null if brand is not set yet
  const allowedModes = BRAND_ALLOWED_MODES[brandSlug] || DEFAULT_ALLOWED_MODES;
  
  const [proformaNumber, setProformaNumber] = useState("");
  const [selectedMode, setSelectedMode] = useState(allowedModes[0] || "");
  const [selectedLines, setSelectedLines] = useState<string[]>(orphanLines.map(l => l.id));
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!proformaNumber) {
      setError("El número de proforma es requerido");
      return;
    }
    if (selectedLines.length === 0) {
      setError("Debes seleccionar al menos una línea");
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      // Endpoint S20B-09
      await api.post(`/api/expedientes/${expedienteId}/proformas/`, {
        proforma_number: proformaNumber,
        mode: selectedMode,
        line_ids: selectedLines
      });
      onRefresh();
      onClose();
    } catch (err: any) {
      console.error("Error creating proforma:", err);
      const detail = err?.response?.data?.detail || err?.response?.data?.error || "Error al crear la proforma";
      setError(detail);
    } finally {
      setSubmitting(false);
    }
  };

  const toggleLine = (id: string) => {
    setSelectedLines(prev => 
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  if (!open) return null;

  return (
    <FormModal
      open={open}
      onClose={onClose}
      title="Nueva Proforma (C3)"
      size="md"
      footer={
        <div className="flex justify-end gap-3 p-4">
          <button className="btn btn-secondary" onClick={onClose} disabled={submitting}>
            Cancelar
          </button>
          <button className="btn btn-primary" onClick={handleSubmit} disabled={submitting}>
            {submitting ? "Creando..." : "Crear Proforma"}
          </button>
        </div>
      }
    >
      <div className="space-y-6">
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 text-red-600 text-sm rounded flex items-center gap-2">
            <AlertCircle size={16} /> {error}
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="caption font-bold text-secondary mb-1 block uppercase tracking-wider">
              Número de Proforma
            </label>
            <input 
              type="text" 
              className="input w-full" 
              placeholder="Ej: PRF-001"
              value={proformaNumber}
              onChange={e => setProformaNumber(e.target.value)}
              disabled={submitting}
            />
          </div>
          <div>
            <label className="caption font-bold text-secondary mb-1 block uppercase tracking-wider">
              Modo Logístico
            </label>
            <select 
              className="input w-full"
              value={selectedMode}
              onChange={e => setSelectedMode(e.target.value)}
              disabled={submitting}
            >
              {allowedModes.map(m => (
                <option key={m} value={m}>{MODE_LABELS[m] || m}</option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="caption font-bold text-secondary mb-3 block uppercase tracking-wider">
            Líneas a Vincular ({selectedLines.length})
          </label>
          <div className="border border-divider rounded overflow-hidden divide-y divide-divider max-h-[300px] overflow-y-auto bg-surface">
            {orphanLines.map(line => (
              <label key={line.id} className="flex items-center gap-3 p-3 hover:bg-bg transition-colors cursor-pointer">
                <input 
                  type="checkbox" 
                  checked={selectedLines.includes(line.id)}
                  onChange={() => toggleLine(line.id)}
                  disabled={submitting}
                  className="rounded border-divider text-primary focus:ring-primary"
                />
                <div className="flex-1">
                  <div className="body-sm font-medium">{line.product_name}</div>
                  <div className="caption text-secondary">
                    Talla: <span className="font-mono">{line.size_display}</span> | Cant: {line.quantity}
                  </div>
                </div>
                <div className="body-sm font-mono text-secondary">${Number(line.unit_price).toFixed(2)}</div>
              </label>
            ))}
            {orphanLines.length === 0 && (
              <div className="text-center py-8 text-secondary body-sm italic bg-bg">
                No hay líneas huérfanas disponibles para asignar.
              </div>
            )}
          </div>
          <p className="caption text-secondary mt-2">
            Solo puedes asignar líneas que no pertenecen a ninguna proforma.
          </p>
        </div>
      </div>
    </FormModal>
  );
}
