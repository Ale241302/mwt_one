"use client";

import { useState } from "react";
import FormModal from "@/components/ui/FormModal";
import api from "@/lib/api";

interface ReassignLineModalProps {
  open: boolean;
  expedienteId: string;
  lineId: string | null;
  proformas: any[];
  onClose: () => void;
  onSuccess: () => void;
}

export default function ReassignLineModal({
  open,
  expedienteId,
  lineId,
  proformas,
  onClose,
  onSuccess,
}: ReassignLineModalProps) {
  const [selectedProformaId, setSelectedProformaId] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!open || !lineId) return null;

  const handleSubmit = async () => {
    if (!selectedProformaId) return;
    setLoading(true);
    setError(null);
    try {
      await api.post(`/expedientes/${expedienteId}/command/C_REASSIGN_LINE/`, {
        line_id: lineId,
        proforma_id: selectedProformaId,
      });
      onSuccess();
      onClose();
      setSelectedProformaId("");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Error al reasignar línea");
    } finally {
      setLoading(false);
    }
  };

  const footer = (
    <div className="flex justify-end gap-3 w-full">
      <button className="btn btn-secondary" onClick={onClose} disabled={loading}>
        Cancelar
      </button>
      <button
        className="btn btn-primary bg-navy text-white hover:bg-navy-dark px-4 py-2 rounded-md transition-colors"
        onClick={handleSubmit}
        disabled={loading || !selectedProformaId}
      >
        {loading ? "Moviendo..." : "Mover Línea"}
      </button>
    </div>
  );

  return (
    <FormModal open={open} onClose={onClose} title="Mover Línea a Proforma" footer={footer} size="sm">
      {error && (
        <div className="p-3 mb-4 rounded-lg bg-red-50 text-red-600 text-sm border border-red-200">
          {error}
        </div>
      )}
      <div className="space-y-4">
        <p className="text-sm text-gray-600">
          Selecciona la proforma destino para asignar esta línea.
        </p>
        <select
          className="w-full px-3 py-2 border border-divider rounded-md focus:border-navy focus:ring-1 focus:ring-navy outline-none text-sm"
          value={selectedProformaId}
          onChange={(e) => setSelectedProformaId(e.target.value)}
          disabled={loading}
        >
          <option value="" disabled>
            -- Selecciona una proforma --
          </option>
          {proformas.map((p) => {
            const displayId = p.payload?.proforma_number || (p.id || p.artifact_id || "").split("-")[0];
            return (
              <option key={p.id || p.artifact_id} value={p.id || p.artifact_id}>
                Proforma {displayId}
              </option>
            );
          })}
        </select>
      </div>
    </FormModal>
  );
}
