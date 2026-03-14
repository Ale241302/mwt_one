/**
 * S9 — ArtifactModal (ruta canónica: /components/modals/)
 * Modal para registrar un artefacto dentro de un expediente.
 * Reutilizar desde ArtifactAccordion — nunca duplicar.
 */
"use client";
import { useState } from "react";
import { X, Loader2, CheckCircle } from "lucide-react";

interface ArtifactModalProps {
  artifactId: string;
  artifactName: string;
  expedienteId: string;
  onClose: () => void;
  onSuccess: () => void;
}

export function ArtifactModal({
  artifactId,
  artifactName,
  expedienteId,
  onClose,
  onSuccess,
}: ArtifactModalProps) {
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState<string | null>(null);
  const [success, setSuccess]   = useState(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const formData = new FormData(e.currentTarget);
    const payload  = Object.fromEntries(formData.entries());

    try {
      const res = await fetch(
        `/api/expedientes/${expedienteId}/artifacts/${artifactId}/register/`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }
      );
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail ?? data.message ?? "Error al registrar artefacto");
      }
      setSuccess(true);
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 800);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error inesperado");
    } finally {
      setLoading(false);
    }
  }

  return (
    // Backdrop
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="artifact-modal-title"
    >
      <div className="bg-[var(--surface)] rounded-2xl shadow-[var(--shadow-lg)] w-full max-w-md p-6 mx-4">
        {/* ── Header ── */}
        <div className="flex items-center justify-between mb-4">
          <h2
            id="artifact-modal-title"
            className="text-base font-semibold text-[var(--navy)]"
          >
            {artifactName}
          </h2>
          <button
            onClick={onClose}
            aria-label="Cerrar modal"
            className="p-1.5 rounded-lg hover:bg-[var(--surface-hover)] transition-colors"
          >
            <X size={16} className="text-[var(--text-tertiary)]" />
          </button>
        </div>

        {/* ── Success state ── */}
        {success ? (
          <div className="flex flex-col items-center gap-3 py-6">
            <CheckCircle size={40} className="text-[var(--success)]" />
            <p className="text-sm font-medium text-[var(--text-primary)]">Artefacto registrado</p>
          </div>
        ) : (
          // ── Form ──
          <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            <div>
              <label
                htmlFor="artifact-notes"
                className="block text-xs font-medium text-[var(--text-secondary)] mb-1"
              >
                Notas / referencia
              </label>
              <input
                id="artifact-notes"
                name="notes"
                type="text"
                autoFocus
                className="w-full border border-[var(--border)] rounded-lg px-3 py-2 text-sm bg-[var(--surface)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--navy)] focus:border-transparent placeholder:text-[var(--text-disabled)] transition"
                placeholder="Referencia o comentario..."
              />
            </div>

            {/* Error */}
            {error && (
              <div className="bg-[var(--coral-soft)] border border-[var(--coral)]/30 rounded-lg px-3 py-2 text-xs text-[var(--coral)]">
                {error}
              </div>
            )}

            {/* Actions */}
            <div className="flex justify-end gap-2 mt-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-[var(--text-secondary)] hover:bg-[var(--surface-hover)] rounded-lg transition-colors"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 text-sm font-semibold bg-[var(--navy)] text-[var(--text-inverse)] rounded-lg hover:bg-[var(--navy-light)] transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                {loading && <Loader2 size={14} className="animate-spin" aria-hidden />}
                Registrar
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
