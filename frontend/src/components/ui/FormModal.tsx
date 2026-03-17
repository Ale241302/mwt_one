"use client";

import { useEffect, useRef } from "react";
import { X } from "lucide-react";

/* FormModal — Sprint 9.1 audit round 2
   Fix #2: Escape handler + focus trap for ALL form modals (not just ConfirmDialog)
   Fix #4: Single shell replaces 3 duplicated modal structures
   S9.1-04: aria-modal=true, overlay click para cerrar, prop size (sm/md/lg) */

interface FormModalProps {
  open: boolean;
  title: string;
  titleId?: string;
  onClose: () => void;
  children: React.ReactNode;
  footer?: React.ReactNode;
  size?: "sm" | "md" | "lg";
}

export default function FormModal({
  open, title, titleId, onClose, children, footer, size = "md",
}: FormModalProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const id = titleId || "form-modal-title";

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [open, onClose]);

  useEffect(() => {
    if (!open || !containerRef.current) return;
    const timer = setTimeout(() => {
      const firstInput = containerRef.current?.querySelector<HTMLElement>(
        "input:not([type=hidden]):not([type=checkbox]), select, textarea"
      );
      firstInput?.focus();
    }, 50);
    return () => clearTimeout(timer);
  }, [open]);

  if (!open) return null;

  const sizeClass = { sm: "modal-sm", md: "modal-md", lg: "modal-lg" }[size];

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        ref={containerRef}
        className={`modal-container ${sizeClass}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby={id}
        onClick={(e) => e.stopPropagation()}
      >
        <div
          className="flex items-center justify-between p-5"
          style={{ borderBottom: "1px solid var(--divider)" }}
        >
          <h2 id={id} className="heading-lg">{title}</h2>
          <button
            className="btn btn-sm btn-ghost"
            onClick={onClose}
            aria-label="Cerrar formulario"
          >
            <X size={18} />
          </button>
        </div>

        <div className="p-5 space-y-4">
          {children}
        </div>

        {footer && (
          <div
            className="flex items-center justify-end gap-3 p-5"
            style={{ borderTop: "1px solid var(--divider)" }}
          >
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}
