"use client";

import { useState } from "react";
import { X, Search, GitMerge, ChevronRight, AlertTriangle } from "lucide-react";
import api from "@/lib/api";
import toast from "react-hot-toast";

// States where merge is allowed — FROZEN
const MERGEABLE_STATES = ["REGISTRO", "PI_SOLICITADA", "CONFIRMADO"];

interface ExpedienteResult {
  id: number | string;
  ref_number?: string;
  custom_ref?: string;
  status: string;
  client_name?: string;
  brand_name?: string;
}

interface Props {
  expedienteId: number | string;
  currentRef: string;
  currentStatus: string;
  brandId?: string | number;
  clientId?: string;
  onClose: () => void;
  onSuccess: () => void;
}

export default function ModalMerge({
  expedienteId,
  currentRef,
  currentStatus,
  brandId,
  clientId,
  onClose,
  onSuccess,
}: Props) {
  const [step, setStep] = useState<1 | 2>(1);
  const [searchQuery, setSearchQuery] = useState("");
  const [results, setResults] = useState<ExpedienteResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [selected, setSelected] = useState<ExpedienteResult | null>(null);
  const [masterId, setMasterId] = useState<number | string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const canMerge = MERGEABLE_STATES.includes(currentStatus);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setSearching(true);
    setResults([]);
    try {
      const params = new URLSearchParams({
        search: searchQuery,
        status__in: MERGEABLE_STATES.join(","),
      });
      if (brandId) params.set("brand", String(brandId));
      if (clientId) params.set("client", clientId);
      const res = await api.get(`expedientes/?${params.toString()}`);
      const list: ExpedienteResult[] = Array.isArray(res.data)
        ? res.data
        : res.data?.results ?? [];
      // Exclude self
      setResults(list.filter((e) => String(e.id) !== String(expedienteId)));
    } catch {
      toast.error("Error al buscar expedientes");
    } finally {
      setSearching(false);
    }
  };

  const handleSelectResult = (result: ExpedienteResult) => {
    setSelected(result);
    setMasterId(expedienteId); // default: current is master
    setStep(2);
  };

  const handleMerge = async () => {
    if (!selected || !masterId) return;
    setSubmitting(true);
    try {
      await api.post(`expedientes/${expedienteId}/merge/`, {
        target_expediente_id: selected.id,
        master_id: masterId,
      });
      toast.success("Expedientes fusionados correctamente");
      onSuccess();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      const msg = e.response?.data?.detail ?? "Error al fusionar expedientes";
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const labelA = currentRef;
  const labelB = selected?.ref_number ?? selected?.custom_ref ?? `#${selected?.id}`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)] shadow-xl w-full max-w-lg">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--color-border)]">
          <div className="flex items-center gap-2">
            <GitMerge className="w-5 h-5 text-[var(--color-navy)]" />
            <h2 className="text-base font-semibold text-[var(--color-text-primary)]">
              Fusionar expediente
            </h2>
          </div>
          <button onClick={onClose} className="p-1.5 rounded hover:bg-[var(--color-bg-alt)] text-[var(--color-text-tertiary)] transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        {!canMerge && (
          <div className="px-6 py-4">
            <div className="flex items-center gap-2 bg-[var(--color-bg-alt)] border border-[var(--color-border)] rounded-lg px-4 py-3">
              <AlertTriangle className="w-4 h-4 text-[var(--color-coral)]" />
              <p className="text-sm text-[var(--color-text-secondary)]">
                Merge solo disponible en estados: {MERGEABLE_STATES.join(", ")}. Estado actual: <strong>{currentStatus}</strong>.
              </p>
            </div>
          </div>
        )}

        {canMerge && (
          <div className="px-6 py-5 space-y-5">
            {/* Step indicator */}
            <div className="flex items-center gap-2 text-xs text-[var(--color-text-tertiary)]">
              <span className={step >= 1 ? "text-[var(--color-navy)] font-semibold" : ""}>1. Buscar expediente</span>
              <ChevronRight className="w-3 h-3" />
              <span className={step >= 2 ? "text-[var(--color-navy)] font-semibold" : ""}>2. Elegir master</span>
            </div>

            {/* Step 1 */}
            {step === 1 && (
              <div className="space-y-3">
                <p className="text-sm text-[var(--color-text-secondary)]">
                  Buscar el expediente destino para fusionar con <strong className="text-[var(--color-navy)]">{labelA}</strong>:
                </p>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--color-text-tertiary)]" />
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                      placeholder="Ref, cliente, marca..."
                      className="w-full pl-8 pr-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg text-sm text-[var(--color-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-navy)]/30"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={handleSearch}
                    disabled={searching}
                    className="px-4 py-2 bg-[var(--color-navy)] text-white text-sm rounded-lg hover:opacity-80 disabled:opacity-50 transition-opacity"
                  >
                    {searching ? <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> : "Buscar"}
                  </button>
                </div>

                {results.length > 0 && (
                  <ul className="border border-[var(--color-border)] rounded-xl overflow-hidden">
                    {results.map((r) => (
                      <li
                        key={r.id}
                        onClick={() => handleSelectResult(r)}
                        className="px-4 py-3 hover:bg-[var(--color-bg-alt)] cursor-pointer border-b last:border-b-0 border-[var(--color-border)] flex items-center justify-between"
                      >
                        <div>
                          <p className="text-sm font-mono font-medium text-[var(--color-navy)]">
                            {r.ref_number ?? r.custom_ref ?? `#${r.id}`}
                          </p>
                          <p className="text-xs text-[var(--color-text-tertiary)]">
                            {r.client_name} · {r.brand_name} · {r.status}
                          </p>
                        </div>
                        <ChevronRight className="w-4 h-4 text-[var(--color-text-tertiary)]" />
                      </li>
                    ))}
                  </ul>
                )}

                {results.length === 0 && searchQuery && !searching && (
                  <p className="text-xs text-[var(--color-text-tertiary)] italic px-1">Sin resultados.</p>
                )}
              </div>
            )}

            {/* Step 2 */}
            {step === 2 && selected && (
              <div className="space-y-4">
                <p className="text-sm text-[var(--color-text-secondary)]">
                  ¿Cuál será el expediente <strong>master</strong>?
                </p>
                <div className="space-y-2">
                  {[expedienteId, selected.id].map((candidateId) => {
                    const isA = String(candidateId) === String(expedienteId);
                    const label = isA ? labelA : labelB;
                    return (
                      <label
                        key={String(candidateId)}
                        className={`flex items-center gap-3 border rounded-xl px-4 py-3 cursor-pointer transition-colors ${
                          String(masterId) === String(candidateId)
                            ? "border-[var(--color-navy)] bg-[var(--color-navy)]/5"
                            : "border-[var(--color-border)] hover:bg-[var(--color-bg-alt)]"
                        }`}
                      >
                        <input
                          type="radio"
                          name="master"
                          value={String(candidateId)}
                          checked={String(masterId) === String(candidateId)}
                          onChange={() => setMasterId(candidateId)}
                          className="accent-[var(--color-navy)]"
                        />
                        <span className="text-sm font-mono font-medium text-[var(--color-navy)]">{label}</span>
                        {String(masterId) === String(candidateId) && (
                          <span className="ml-auto text-xs bg-[var(--color-navy)] text-white rounded px-2 py-0.5">Master</span>
                        )}
                      </label>
                    );
                  })}
                </div>

                <div className="flex justify-between gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setStep(1)}
                    className="text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors"
                  >
                    ← Volver
                  </button>
                  <button
                    type="button"
                    onClick={handleMerge}
                    disabled={submitting || !masterId}
                    className="flex items-center gap-1.5 px-4 py-2 bg-[var(--color-navy)] text-white text-sm rounded-lg hover:opacity-80 disabled:opacity-50 transition-opacity"
                  >
                    {submitting ? <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> : <GitMerge className="w-4 h-4" />}
                    Fusionar
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
