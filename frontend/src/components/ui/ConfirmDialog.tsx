"use client";

import { useEffect, useRef } from "react";
import { AlertTriangle } from "lucide-react";

/* ConfirmDialog — Sprint 9.1 post-audit
   Fix #4: role="alertdialog", aria-modal, aria-labelledby, aria-describedby, autoFocus on cancel
   S9.1-03: z-index: 50 en modal-overlay (via globals.css) */

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: "danger" | "warning";
  loading?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ConfirmDialog({
  open, title, message,
  confirmLabel = "Eliminar", cancelLabel = "Cancelar",
  variant = "danger", loading = false,
  onConfirm, onCancel,
}: ConfirmDialogProps) {
  const cancelRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (open) cancelRef.current?.focus();
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const handleEsc = (e: KeyboardEvent) => { if (e.key === "Escape") onCancel(); };
    document.addEventListener("keydown", handleEsc);
    return () => document.removeEventListener("keydown", handleEsc);
  }, [open, onCancel]);

  if (!open) return null;

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div
        className="modal-container modal-alert"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-title"
        aria-describedby="confirm-message"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="confirm-dialog">
          <div
            className="mx-auto mb-4 flex items-center justify-center rounded-full"
            style={{
              width: 48, height: 48,
              background: variant === "danger" ? "var(--critical-bg)" : "var(--warning-bg)",
            }}
          >
            <AlertTriangle
              size={24}
              style={{ color: variant === "danger" ? "var(--critical)" : "var(--warning)" }}
            />
          </div>
          <h3 id="confirm-title">{title}</h3>
          <p id="confirm-message">{message}</p>
          <div className="confirm-dialog-actions">
            <button ref={cancelRef} className="btn btn-md btn-secondary" onClick={onCancel} disabled={loading}>
              {cancelLabel}
            </button>
            <button className={`btn btn-md ${variant === "danger" ? "btn-danger" : "btn-primary"}`} onClick={onConfirm} disabled={loading}>
              {loading ? "Procesando..." : confirmLabel}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
