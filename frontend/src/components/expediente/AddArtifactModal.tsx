"use client";
import { useState } from "react";
import { Plus, Search, X } from "lucide-react";
import FormModal from "@/components/ui/FormModal";
import { ARTIFACT_UI_REGISTRY } from "@/constants/artifact-ui-registry";

interface AddArtifactModalProps {
  open: boolean;
  onClose: () => void;
  onSelect: (artifactType: string) => void;
  artifacts: any[];
}

const ALL_REGISTRY_TYPES = Object.keys(ARTIFACT_UI_REGISTRY);

export default function AddArtifactModal({
  open,
  onClose,
  onSelect,
  artifacts,
}: AddArtifactModalProps) {
  const [searchTerm, setSearchTerm] = useState("");

  if (!open) return null;

  const existingTypes = new Set(artifacts.map((a) => a.artifact_type));

  const filteredTypes = ALL_REGISTRY_TYPES.filter((t) => {
    const reg = ARTIFACT_UI_REGISTRY[t];
    const search = searchTerm.toLowerCase();
    return (
      t.toLowerCase().includes(search) ||
      reg.label.toLowerCase().includes(search)
    );
  });

  return (
    <FormModal
      open={open}
      onClose={onClose}
      title="Seleccionar artefacto para agregar"
      size="md"
    >
      <div className="space-y-4">
        {/* Search bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary" size={16} />
          <input
            type="text"
            placeholder="Buscar por código (ART-01) o nombre..."
            className="input w-full pl-10"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            autoFocus
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm("")}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary hover:text-text"
            >
              <X size={14} />
            </button>
          )}
        </div>

        {/* List */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-[400px] overflow-y-auto pr-2 pb-4">
          {filteredTypes.map((t) => {
            const reg = ARTIFACT_UI_REGISTRY[t];
            const records = artifacts.filter((a) => a.artifact_type === t).length;

            return (
              <button
                key={t}
                onClick={() => onSelect(t)}
                className="flex flex-col text-left p-4 rounded-xl border border-divider hover:border-amber-300 hover:bg-amber-50/30 transition-all group"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-mono text-[10px] text-text-tertiary bg-surface px-1.5 py-0.5 rounded border border-divider group-hover:border-amber-200">
                    {t}
                  </span>
                  {records > 0 && (
                    <span className="text-[9px] font-bold text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded-full uppercase tabular-nums">
                      {records} registros
                    </span>
                  )}
                </div>
                <span className="text-sm font-semibold text-navy group-hover:text-amber-900">
                  {reg.label}
                </span>
              </button>
            );
          })}

          {filteredTypes.length === 0 && (
            <div className="col-span-full py-12 text-center text-text-tertiary">
              No se encontraron artefactos con &quot;{searchTerm}&quot;
            </div>
          )}
        </div>
      </div>
    </FormModal>
  );
}
