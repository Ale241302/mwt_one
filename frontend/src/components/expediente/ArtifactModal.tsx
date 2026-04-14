"use client";
import { useState, useEffect } from "react";
import { FileText, XCircle, History, ChevronRight, PlusCircle, AlignLeft } from "lucide-react";
import api from "@/lib/api";
import FormModal from "@/components/ui/FormModal";
import { fetchBuilderArtifactStructure } from "@/lib/builderApi";

interface ArtifactModalProps {
  open: boolean;
  expedienteId: string;
  commandKey: string; // Puede ser el slug 'ART-01' o el ID del builder '3'
  artifact?: any; // The existing DB instance, if editing
  readOnly?: boolean;
  onClose: () => void;
  onSuccess: () => void;
  isAdmin?: boolean;
  onNewRecord?: () => void;
  allArtifacts?: any[]; // All existing DB instances for this type
  builderContext?: any[]; // The list of builder artifacts to map name/id if needed
}

type FormData = Record<string, any>;

// Componente para renderizar la estructura JSON
function DynamicFormRenderer({
  structure,
  form,
  setForm,
  isReadOnly,
}: {
  structure: any;
  form: FormData;
  setForm: (f: FormData) => void;
  isReadOnly?: boolean;
}) {
  if (!structure || !structure.sections) return <div className="p-4 text-center text-text-tertiary">Estructura de formulario vacía</div>;

  const set = (k: string, v: any) => {
    if (isReadOnly) return;
    setForm({ ...form, [k]: v });
  };

  return (
    <div className="space-y-6">
      {structure.sections.map((section: any) => (
        <div key={section.id} className="p-3 bg-surface border border-divider rounded-lg shadow-sm space-y-4">
          {section.columns?.map((col: any) => (
            <div key={col.id} className="space-y-4">
              {col.fields?.map((field: any) => {
                // Infer input type mappings
                const isNumber = field.type === "number";
                const isDate = field.type === "date";
                const isCode = field.type === "code";
                const isSelect = field.type === "select";
                const isRadio = field.type === "radio";
                
                const htmlType = isNumber ? "number" : isDate ? "date" : "text";

                // Normalize options since they can be simple strings or objects with a `label`
                const normalizedOptions = (field.options || []).map((opt: any) => {
                  if (typeof opt === 'string') return { value: opt, label: opt };
                  return { value: opt.label, label: opt.label };
                });

                return (
                  <div key={field.id} className="space-y-1">
                    <label className="th-label block font-semibold text-navy">
                      {field.label}
                    </label>
                    {isSelect ? (
                      <select
                        className="input w-full"
                        value={form[field.id] || ""}
                        onChange={(e) => set(field.id, e.target.value)}
                        disabled={isReadOnly}
                      >
                        <option value="">-- Seleccionar --</option>
                        {normalizedOptions.map((opt: any, i: number) => (
                          <option key={i} value={opt.value}>{opt.label}</option>
                        ))}
                      </select>
                    ) : isRadio ? (
                      <div className="flex flex-col gap-2 mt-1">
                        {normalizedOptions.map((opt: any, idx: number) => (
                          <label key={idx} className="flex items-center gap-2 cursor-pointer text-sm">
                            <input
                              type="radio"
                              name={field.id}
                              value={opt.value}
                              checked={form[field.id] === opt.value}
                              onChange={(e) => set(field.id, e.target.value)}
                              disabled={isReadOnly}
                              className="w-4 h-4 text-primary bg-bg border-gray-300 focus:ring-primary"
                            />
                            <span>{opt.label}</span>
                          </label>
                        ))}
                      </div>
                    ) : isCode ? (
                      <textarea
                        className="input w-full font-mono text-sm h-32"
                        placeholder="Escribe aquí..."
                        value={String(form[field.id] ?? "")}
                        onChange={(e) => set(field.id, e.target.value)}
                        disabled={isReadOnly}
                      />
                    ) : (
                      <input
                        type={field.type === 'file' ? 'text' : htmlType}
                        className="input w-full"
                        placeholder={field.type === 'file' ? 'Adjuntar archivo no soportado aún, ingresa URL' : ''}
                        value={String(form[field.id] ?? "")}
                        onChange={(e) => set(field.id, isNumber ? Number(e.target.value) : e.target.value)}
                        disabled={isReadOnly}
                      />
                    )}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

export default function ArtifactModal({
  open,
  expedienteId,
  commandKey,
  artifact,
  readOnly: readOnlyProp,
  onClose,
  onSuccess,
  isAdmin,
  onNewRecord,
  allArtifacts,
  builderContext,
}: ArtifactModalProps) {
  const isReadOnly = readOnlyProp === true;

  const [activeTab, setActiveTab] = useState<"form" | "history">("form");
  const [form, setForm] = useState<FormData>(artifact?.payload || {});
  const [structureRaw, setStructureRaw] = useState<any>(null);
  const [modalTitle, setModalTitle] = useState("Cargando artefacto...");
  const [actualBuilderId, setActualBuilderId] = useState<string | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize fields
  useEffect(() => {
    if (open) {
      setForm(artifact?.payload || {});
      setActiveTab("form");
    }
  }, [open, artifact]);

  // Fetch Structure
  useEffect(() => {
    if (open && commandKey) {
      // Find builder ID from context if commandKey is something like "ART-18" or an actual ID
      let matchedId = commandKey;
      let matchedTitle = commandKey;

      if (builderContext) {
        const found = builderContext.find(b => b.id.toString() === commandKey || b.title.startsWith(commandKey));
        if (found) {
          matchedId = found.id.toString();
          matchedTitle = found.title;
        }
      }

      setModalTitle(isReadOnly ? `Detalle — ${matchedTitle}` : `Editar — ${matchedTitle}`);
      setActualBuilderId(matchedId);

      fetchBuilderArtifactStructure(matchedId).then((res) => {
        if (res && res.structure_json) {
          setStructureRaw(res.structure_json);
        } else {
          setError("No se pudo obtener la estructura de Formulario.");
        }
      });
    }
  }, [open, commandKey, builderContext, isReadOnly]);

  if (!open) return null;

  const historyEntries = (allArtifacts || []).filter(
    (a) => !artifact || a !== artifact
  );

  const handleSubmit = async () => {
    if (!expedienteId) {
      setError("Error: ID de expediente no disponible.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      if (artifact?.artifact_id) {
        // Edit mode (PUT)
        await api.put(`/expedientes/${expedienteId}/artifacts/dynamic/${artifact.artifact_id}/`, { payload: form });
      } else {
        // Create mode (POST)
        // Guardamos el tipo como el string principal (ej ART-18 o el ID si no hay de otra)
        const typeToSave = commandKey; 
        await api.post(`/expedientes/${expedienteId}/artifacts/dynamic/`, { artifact_type: typeToSave, payload: form });
      }
      onSuccess();
      onClose();
    } catch (err: any) {
      const errData = err?.response?.data;
      setError(
        errData
          ? Object.entries(errData)
            .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(", ") : v}`)
            .join(" | ")
          : "Error al guardar el artefacto."
      );
    } finally {
      setLoading(false);
    }
  };

  const showTabs = isReadOnly && historyEntries.length > 0;

  const footerContent = (
    <div className="flex items-center justify-between w-full gap-2">
      <div className="flex items-center gap-2">
        {isReadOnly && onNewRecord && (
          <button
            className="btn btn-sm btn-ghost border border-primary text-primary flex items-center gap-1"
            onClick={() => { onClose(); onNewRecord(); }}
            disabled={loading}
          >
            <PlusCircle size={13} /> Nuevo registro
          </button>
        )}
      </div>
      <div className="flex items-center gap-2">
        <button className="btn btn-md btn-secondary" onClick={onClose} disabled={loading}>
          {isReadOnly ? "Cerrar" : "Cancelar"}
        </button>
        {!isReadOnly && (
          <button
            className="btn btn-md btn-primary text-white"
            onClick={handleSubmit}
            disabled={loading || !structureRaw}
          >
            {loading ? "Guardando..." : "Guardar Registro"}
          </button>
        )}
      </div>
    </div>
  );

  return (
    <FormModal
      open={open}
      title={modalTitle}
      onClose={onClose}
      footer={footerContent}
      size="md"
    >
      {showTabs && (
        <div className="flex gap-1 mb-4 border-b border-divider">
          <button
            onClick={() => setActiveTab("form")}
            className={`px-4 py-2 text-sm font-medium transition-colors ${activeTab === "form"
                ? "border-b-2 border-primary text-primary"
                : "text-text-tertiary hover:text-text"
              }`}
          >
            Registro actual
          </button>
          <button
            onClick={() => setActiveTab("history")}
            className={`px-4 py-2 text-sm font-medium flex items-center gap-1 transition-colors ${activeTab === "history"
                ? "border-b-2 border-primary text-primary"
                : "text-text-tertiary hover:text-text"
              }`}
          >
            <History size={13} />
            Historial
            <span className="ml-1 text-[10px] bg-slate-100 text-slate-600 rounded-full px-1.5">
              {historyEntries.length}
            </span>
          </button>
        </div>
      )}

      {activeTab === "history" ? (
        <div className="space-y-2">
          {historyEntries.length === 0 ? (
            <p className="text-sm text-text-tertiary py-4 text-center">
              No hay registros previos.
            </p>
          ) : (
            historyEntries.map((h, i) => (
              <div
                key={i}
                className="flex items-center justify-between p-3 rounded-lg border border-divider hover:bg-bg transition-colors cursor-pointer"
                onClick={() => {
                  setActiveTab("form");
                  setForm(h.payload || {});
                }}
              >
                <div className="flex items-center gap-2">
                  <span className="text-text-tertiary text-[11px]">{i + 1}.</span>
                  <span
                    className={`badge text-[10px] px-1.5 py-0.5 ${h.status === "COMPLETED" || h.status === "completed"
                        ? "badge-success"
                        : h.status === "VOIDED" || h.status === "voided"
                          ? "badge-critical"
                          : "badge-info"
                      }`}
                  >
                    {h.status}
                  </span>
                  <span className="text-text-tertiary text-[11px]">
                    {new Date(h.created_at).toLocaleDateString("es-CO", {
                      day: "2-digit",
                      month: "short",
                      year: "numeric",
                    })}
                  </span>
                </div>
                <ChevronRight size={14} className="text-text-tertiary" />
              </div>
            ))
          )}
        </div>
      ) : (
        <>
          {isReadOnly && (
            <div className="mb-4 px-3 py-2 rounded-lg bg-bg border border-divider text-xs text-text-tertiary">
              Registro en solo lectura.
              {onNewRecord
                ? ' Usa el botón "Nuevo registro" para agregar uno adicional.'
                : ' Usa "Nuevo registro" en el artefacto para actualizarlo.'}
            </div>
          )}
          {error && (
            <div className="p-3 mb-4 rounded-lg bg-coral-soft/20 border border-coral/30 text-sm text-coral">
              {error}
            </div>
          )}

          {!structureRaw ? (
            <div className="py-8 text-center text-text-tertiary">Cargando esquema...</div>
          ) : (
            <DynamicFormRenderer
              structure={structureRaw}
              form={form}
              setForm={setForm}
              isReadOnly={isReadOnly}
            />
          )}
        </>
      )}
    </FormModal>
  );
}
