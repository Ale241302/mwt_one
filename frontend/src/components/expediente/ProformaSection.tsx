"use client";

import { EXPEDIENTE_LEVEL_ARTIFACTS } from "@/constants/proforma-artifact-policy";
import { resolveProformaPolicy } from "@/utils/resolve-proforma-policy";
import ArtifactSection, { ArtifactPolicyState } from "./ArtifactSection";
import { Package } from "lucide-react";

interface ProformaSectionProps {
  proforma: any;
  brandSlug: string;
  currentState: string;
  lines: any[];
  childArtifacts: any[];
  availableActions: any;
  onActionClick: (commandKey: string, artifact?: any) => void;
  hasAction: (commandKey: string) => boolean;
  onReassignLine?: (lineId: string) => void;
  isEditable?: boolean;
}

export default function ProformaSection({
  proforma,
  brandSlug,
  currentState,
  lines,
  childArtifacts,
  availableActions,
  onActionClick,
  hasAction,
  onReassignLine,
  isEditable,
}: ProformaSectionProps) {
  const { payload } = proforma;
  const mode = payload?.mode || "default";

  const rawPolicy = resolveProformaPolicy(brandSlug, mode, currentState);
  
  const proformaPolicy: ArtifactPolicyState = {
    required: rawPolicy.required.filter((a) => !EXPEDIENTE_LEVEL_ARTIFACTS.has(a)),
    optional: rawPolicy.optional.filter((a) => !EXPEDIENTE_LEVEL_ARTIFACTS.has(a)),
    gate_for_advance: rawPolicy.gate_for_advance.filter((a) => !EXPEDIENTE_LEVEL_ARTIFACTS.has(a)),
  };

  const isModeC = mode === "mode_c";
  const modeBadgeColor =
    mode === "mode_c"
      ? "bg-emerald-100 text-emerald-800 border-emerald-200"
      : mode === "mode_b"
      ? "bg-blue-100 text-blue-800 border-blue-200"
      : "bg-gray-100 text-gray-800 border-gray-200";

  const modeText = mode === "mode_c" ? "FULL" : mode === "mode_b" ? "Comisión" : "Normal";

  return (
    <div className="card overflow-hidden my-4 border border-[var(--border)] shadow-sm">
      <div className="px-5 py-4 border-b border-divider bg-[var(--surface-hover)] flex justify-between items-center">
        <div className="flex items-center gap-3">
          <span className="font-semibold text-navy text-base">
            Proforma {payload?.proforma_number || proforma.id.split("-")[0]}
          </span>
          <span className={`px-2 py-0.5 rounded text-[11px] font-medium border ${modeBadgeColor}`}>
            {modeText}
          </span>
          {isModeC && payload?.operated_by && (
            <span className="text-xs text-text-tertiary">
              Opera: <span className="font-medium text-text-secondary">{payload.operated_by}</span>
            </span>
          )}
        </div>
      </div>

      <div className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm whitespace-nowrap">
            <thead className="bg-[var(--bg)] text-text-tertiary text-xs border-b border-divider">
              <tr>
                <th className="px-5 py-2 font-medium">Producto</th>
                <th className="px-5 py-2 font-medium">Talla/Variante</th>
                <th className="px-5 py-2 font-medium text-right">Cant.</th>
                <th className="px-5 py-2 font-medium text-right">Precio Un.</th>
                <th className="px-5 py-2 font-medium text-right">Subtotal</th>
                {isEditable && <th className="px-5 py-2 font-medium text-center">Acciones</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-divider">
              {lines.length === 0 ? (
                <tr>
                  <td colSpan={isEditable ? 6 : 5} className="px-5 py-6 text-center text-text-tertiary text-sm">
                    No hay líneas asignadas a esta proforma.
                  </td>
                </tr>
              ) : (
                lines.map((line) => (
                  <tr key={line.id} className="hover:bg-[var(--surface-hover)] transition-colors">
                    <td className="px-5 py-2 flex items-center gap-2">
                      <Package size={14} className="text-text-tertiary" />
                      <span className="font-medium truncate max-w-[150px]">{line.product_name ?? "—"}</span>
                    </td>
                    <td className="px-5 py-2 text-text-secondary">{line.size ?? "—"}</td>
                    <td className="px-5 py-2 text-right">{line.quantity}</td>
                    <td className="px-5 py-2 text-right">
                      {line.unit_price ? `$${Number(line.unit_price).toFixed(2)}` : "—"}
                    </td>
                    <td className="px-5 py-2 text-right font-medium">
                      {line.total_price ? `$${Number(line.total_price).toFixed(2)}` : "—"}
                    </td>
                    {isEditable && (
                      <td className="px-5 py-2 text-center">
                        <button
                          className="btn btn-sm btn-ghost text-primary text-[11px] py-1 px-2"
                          onClick={() => onReassignLine?.(line.id)}
                        >
                          Mover
                        </button>
                      </td>
                    )}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {(proformaPolicy.required.length > 0 || proformaPolicy.optional.length > 0) && (
        <div className="border-t border-divider">
          <div className="px-5 py-2 bg-[var(--bg)] text-xs font-semibold text-text-tertiary uppercase tracking-wider">
            Requerimientos Operativos
          </div>
          <ArtifactSection
            policyState={proformaPolicy}
            artifacts={childArtifacts}
            availableActions={availableActions}
            onExecute={onActionClick}
            hasAction={hasAction}
          />
        </div>
      )}
    </div>
  );
}
