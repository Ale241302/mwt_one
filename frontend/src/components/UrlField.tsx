"use client";

import { useState } from "react";
import { ExternalLink, Pencil, Trash2, Upload, HelpCircle, X, Check } from "lucide-react";

export interface UrlFieldProps {
  url: string | null;
  label: string;
  onUpdate: (newUrl: string) => void;
  onDelete: () => void;
  uploadEndpoint?: string;
  readOnly?: boolean;
}

export default function UrlField({
  url,
  label,
  onUpdate,
  onDelete,
  uploadEndpoint,
  readOnly = false,
}: UrlFieldProps) {
  const [editing, setEditing] = useState(false);
  const [inputValue, setInputValue] = useState("");
  const [showHelp, setShowHelp] = useState(false);
  const [uploading, setUploading] = useState(false);

  const handleEditStart = () => {
    setInputValue(url ?? "");
    setEditing(true);
  };

  const handleEditConfirm = () => {
    if (inputValue.trim()) {
      onUpdate(inputValue.trim());
    }
    setEditing(false);
  };

  const handleEditCancel = () => {
    setEditing(false);
    setInputValue("");
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!uploadEndpoint || !e.target.files?.[0]) return;
    const file = e.target.files[0];
    const formData = new FormData();
    formData.append("file", file);
    setUploading(true);
    try {
      const res = await fetch(uploadEndpoint, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (data?.url) onUpdate(data.url);
    } catch {
      // upload failed silently — user can paste URL manually
    } finally {
      setUploading(false);
    }
  };

  // ── STATE 1: URL exists ──
  if (url && !editing) {
    return (
      <div className="flex flex-col gap-1">
        <span className="text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">
          {label}
        </span>
        <div className="flex items-center gap-2 flex-wrap">
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-sm text-[var(--color-navy)] hover:underline truncate max-w-xs"
          >
            <ExternalLink className="w-3.5 h-3.5 flex-shrink-0" />
            <span className="truncate">{url}</span>
          </a>
          {!readOnly && (
            <>
              <button
                type="button"
                onClick={handleEditStart}
                className="p-1 rounded hover:bg-[var(--color-bg-alt)] text-[var(--color-text-tertiary)] hover:text-[var(--color-text-primary)] transition-colors"
                title="Editar URL"
              >
                <Pencil className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={onDelete}
                className="p-1 rounded hover:bg-[var(--color-bg-alt)] text-[var(--color-text-tertiary)] hover:text-[var(--color-coral)] transition-colors"
                title="Eliminar URL"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </>
          )}
          <button
            type="button"
            onClick={() => setShowHelp((v) => !v)}
            className="p-1 rounded hover:bg-[var(--color-bg-alt)] text-[var(--color-text-tertiary)] transition-colors"
            title="¿Link no funciona?"
          >
            <HelpCircle className="w-3.5 h-3.5" />
          </button>
        </div>
        {showHelp && (
          <p className="text-xs text-[var(--color-text-tertiary)] bg-[var(--color-bg-alt)] border border-[var(--color-border)] rounded px-2 py-1.5 mt-1">
            ¿Link no funciona? Solicitá link nuevo al admin o editá la URL manualmente.
          </p>
        )}
      </div>
    );
  }

  // ── Editing mode ──
  if (editing) {
    return (
      <div className="flex flex-col gap-1">
        <span className="text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">
          {label}
        </span>
        <div className="flex items-center gap-2">
          <input
            type="url"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="https://..."
            className="flex-1 bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm text-[var(--color-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-navy)]/30"
            autoFocus
            onKeyDown={(e) => {
              if (e.key === "Enter") handleEditConfirm();
              if (e.key === "Escape") handleEditCancel();
            }}
          />
          <button
            type="button"
            onClick={handleEditConfirm}
            className="p-1.5 rounded bg-[var(--color-navy)] text-white hover:opacity-80 transition-opacity"
          >
            <Check className="w-4 h-4" />
          </button>
          <button
            type="button"
            onClick={handleEditCancel}
            className="p-1.5 rounded hover:bg-[var(--color-bg-alt)] text-[var(--color-text-tertiary)] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
    );
  }

  // ── STATE 2/3: URL null ──
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">
        {label}
      </span>
      <div className="flex items-center gap-2 flex-wrap">
        {!readOnly && (
          <>
            <button
              type="button"
              onClick={handleEditStart}
              className="flex items-center gap-1.5 text-xs text-[var(--color-text-secondary)] border border-dashed border-[var(--color-border)] rounded-lg px-3 py-1.5 hover:border-[var(--color-navy)] hover:text-[var(--color-navy)] transition-colors"
            >
              <Pencil className="w-3 h-3" /> Pegar URL
            </button>
            {uploadEndpoint && (
              <label className="flex items-center gap-1.5 text-xs text-[var(--color-text-secondary)] border border-dashed border-[var(--color-border)] rounded-lg px-3 py-1.5 hover:border-[var(--color-navy)] hover:text-[var(--color-navy)] transition-colors cursor-pointer">
                {uploading ? (
                  <div className="w-3 h-3 border-2 border-[var(--color-navy)] border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Upload className="w-3 h-3" />
                )}
                Subir archivo
                <input type="file" className="hidden" onChange={handleUpload} disabled={uploading} />
              </label>
            )}
          </>
        )}
        {readOnly && (
          <span className="text-xs text-[var(--color-text-tertiary)] italic">Sin documento</span>
        )}
      </div>
    </div>
  );
}
