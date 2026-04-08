"use client";

/**
 * S25-12 — FamilyBanner: Muestra la relación parent/child del expediente.
 * - Si es parent: muestra lista de hijos (children links)
 * - Si es child: muestra link al parent
 * - Si is_inverted_child: badge especial indicando inversión de jerarquía
 * Complementa a MergedBanner (que es para fusiones, no splits).
 */

import Link from "next/link";
import { GitBranch, ArrowUpRight, Layers } from "lucide-react";
import { cn } from "@/lib/utils";

interface ExpedienteRef {
  /** UUID del expediente */
  expediente_id: string;
  /** Referencia legible (ref_number o custom_ref) */
  ref_number?: string;
  custom_ref?: string;
}

interface Props {
  /** El expediente actual */
  currentId: string;
  /** Si este expediente es hijo → mostrar el parent */
  parentExpediente?: ExpedienteRef | null;
  /** Si este expediente es padre → mostrar los hijos */
  childExpedientes?: ExpedienteRef[];
  /** Si la jerarquía fue invertida (invert_parent=True) */
  isInvertedChild?: boolean;
  /** Lang para links internos */
  lang?: string;
}

function refLabel(ref: ExpedienteRef): string {
  return ref.ref_number ?? ref.custom_ref ?? `#${ref.expediente_id.slice(0, 8)}`;
}

export default function FamilyBanner({
  currentId,
  parentExpediente,
  childExpedientes = [],
  isInvertedChild = false,
  lang = "es",
}: Props) {
  const hasParent = !!parentExpediente;
  const hasChildren = childExpedientes.length > 0;

  if (!hasParent && !hasChildren) return null;

  return (
    <div className="space-y-2">
      {/* IS CHILD: muestra parent */}
      {hasParent && (
        <div
          className={cn(
            "flex items-start gap-3 rounded-xl border px-4 py-3",
            isInvertedChild
              ? "bg-violet-50 border-violet-200"
              : "bg-sky-50 border-sky-200"
          )}
        >
          <ArrowUpRight
            className={cn(
              "w-4 h-4 mt-0.5 flex-shrink-0",
              isInvertedChild ? "text-violet-500" : "text-sky-500"
            )}
          />
          <div className="flex-1 min-w-0">
            <p
              className={cn(
                "text-xs font-semibold mb-1",
                isInvertedChild ? "text-violet-700" : "text-sky-700"
              )}
            >
              {isInvertedChild
                ? "Expediente hijo (jerarquía invertida)"
                : "Expediente hijo de:"}
            </p>
            <Link
              href={`/${lang}/expedientes/${parentExpediente!.expediente_id}`}
              className={cn(
                "text-xs font-mono hover:underline font-medium",
                isInvertedChild ? "text-violet-700" : "text-sky-700"
              )}
            >
              {refLabel(parentExpediente!)}
            </Link>
            {isInvertedChild && (
              <p className="text-[10px] text-violet-500 mt-0.5">
                La jerarquía fue invertida en la separación de productos.
              </p>
            )}
          </div>
        </div>
      )}

      {/* IS PARENT: muestra hijos */}
      {hasChildren && (
        <div className="flex items-start gap-3 bg-teal-50 border border-teal-200 rounded-xl px-4 py-3">
          <Layers className="w-4 h-4 text-teal-500 mt-0.5 flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-teal-700 mb-1.5">
              Expediente padre — {childExpedientes.length} expediente
              {childExpedientes.length !== 1 ? "s" : ""} hijo
              {childExpedientes.length !== 1 ? "s" : ""}:
            </p>
            <div className="flex flex-wrap gap-1.5">
              {childExpedientes.map((child) => (
                child.expediente_id !== currentId && (
                  <Link
                    key={child.expediente_id}
                    href={`/${lang}/expedientes/${child.expediente_id}`}
                    className="text-xs text-teal-700 hover:underline font-mono bg-white border border-teal-200 rounded px-2 py-0.5"
                  >
                    <GitBranch className="w-3 h-3 inline-block mr-1 opacity-60" />
                    {refLabel(child)}
                  </Link>
                )
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
