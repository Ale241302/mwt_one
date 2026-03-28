"use client";

import Link from "next/link";
import { GitMerge } from "lucide-react";

interface MergedRef {
  id: number | string;
  ref_number?: string;
  custom_ref?: string;
  is_master?: boolean;
}

interface Props {
  mergedWith: MergedRef[];
  currentId: number | string;
  isMaster?: boolean;
  lang?: string;
}

export default function MergedBanner({ mergedWith, currentId, isMaster = false, lang = "es" }: Props) {
  if (!mergedWith || mergedWith.length === 0) return null;

  return (
    <div className="flex items-start gap-3 bg-[var(--color-bg-alt)] border border-[var(--color-border)] rounded-xl px-4 py-3">
      <GitMerge className="w-4 h-4 text-[var(--color-navy)] mt-0.5 flex-shrink-0" />
      <div className="flex-1 min-w-0">
        {isMaster ? (
          <>
            <p className="text-sm font-semibold text-[var(--color-text-primary)] mb-1">
              Expediente master — fusionado con:
            </p>
            <div className="flex flex-wrap gap-2">
              {mergedWith.map((ref) => (
                <Link
                  key={ref.id}
                  href={`/${lang}/expedientes/${ref.id}`}
                  className="text-xs text-[var(--color-navy)] hover:underline font-mono bg-[var(--color-surface)] border border-[var(--color-border)] rounded px-2 py-0.5"
                >
                  {ref.ref_number ?? ref.custom_ref ?? `#${ref.id}`}
                </Link>
              ))}
            </div>
          </>
        ) : (
          <>
            <p className="text-sm text-[var(--color-text-secondary)]">
              Este expediente fue fusionado.
            </p>
            <p className="text-xs text-[var(--color-text-tertiary)] mt-0.5">
              Ver master:{" "}
              {mergedWith
                .filter((r) => r.is_master)
                .map((ref) => (
                  <Link
                    key={ref.id}
                    href={`/${lang}/expedientes/${ref.id}`}
                    className="text-[var(--color-navy)] hover:underline font-mono"
                  >
                    {ref.ref_number ?? ref.custom_ref ?? `#${ref.id}`}
                  </Link>
                ))}
            </p>
          </>
        )}
      </div>
    </div>
  );
}
