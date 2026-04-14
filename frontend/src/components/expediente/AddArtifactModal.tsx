"use client";
import { useState, useEffect } from "react";
import { Plus, Search, X } from "lucide-react";
import FormModal from "@/components/ui/FormModal";
import { fetchBuilderArtifacts } from "@/lib/builderApi";

interface AddArtifactModalProps {
  open: boolean;
  onClose: () => void;
  onSelect: (builderId: string, title?: string) => void;
  artifacts: any[];
}

export default function AddArtifactModal({
  open,
  onClose,
  onSelect,
  artifacts,
}: AddArtifactModalProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [builderTypes, setBuilderTypes] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (open) {
      setIsLoading(true);
      fetchBuilderArtifacts()
        .then((res) => {
          setBuilderTypes(res?.results || []);
          setIsLoading(false);
        })
        .catch(() => setIsLoading(false));
    }
  }, [open]);

  if (!open) return null;

  const existingTypesCount = artifacts.reduce((acc, a) => {
    acc[a.artifact_type] = (acc[a.artifact_type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const filteredTypes = builderTypes.filter((t: any) => {
    const search = searchTerm.toLowerCase();
    return (
      (t.title || "").toLowerCase().includes(search) ||
      (t.id?.toString() || "").includes(search)
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
            placeholder="Buscar por nombre..."
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
          {isLoading ? (
            <div className="col-span-full py-12 text-center text-text-tertiary">
              Cargando artefactos...
            </div>
          ) : filteredTypes.map((t) => {
            const records = existingTypesCount[t.id?.toString()] || 0;

            return (
              <button
                key={t.id}
                onClick={() => onSelect(t.id?.toString(), t.title)}
                className="flex flex-col text-left p-4 rounded-xl border border-divider hover:border-amber-300 hover:bg-amber-50/30 transition-all group"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-mono text-[10px] text-text-tertiary bg-surface px-1.5 py-0.5 rounded border border-divider group-hover:border-amber-200">
                    ID-{t.id}
                  </span>
                  {records > 0 && (
                    <span className="text-[9px] font-bold text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded-full uppercase tabular-nums">
                      {records} registros
                    </span>
                  )}
                </div>
                <span className="text-sm font-semibold text-navy group-hover:text-amber-900">
                  {t.title}
                </span>
              </button>
            );
          })}

          {!isLoading && filteredTypes.length === 0 && (
            <div className="col-span-full py-12 text-center text-text-tertiary">
              No se encontraron artefactos con &quot;{searchTerm}&quot;
            </div>
          )}
        </div>
      </div>
    </FormModal>
  );
}
