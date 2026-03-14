"use client";
import { CanonicalState } from "@/lib/constants/states";
import { ExpedienteCard } from "./PipelineView";
import { PipelineCard } from "./PipelineCard";

interface PipelineColumnProps {
  state: CanonicalState;
  label: string;
  cards: ExpedienteCard[];
}

export function PipelineColumn({ state, label, cards }: PipelineColumnProps) {
  return (
    <div className="flex flex-col w-64 min-w-[256px]">
      {/* ── Column header ── */}
      <div className="flex items-center justify-between mb-2 px-1">
        <span className="text-xs font-semibold uppercase tracking-[0.5px] text-[var(--text-tertiary)]">
          {label}
        </span>
        <span className="text-xs bg-[var(--bg-alt)] text-[var(--text-tertiary)] px-1.5 py-0.5 rounded-full font-medium">
          {cards.length}
        </span>
      </div>

      {/* ── Cards ── */}
      <div className="flex flex-col gap-2 flex-1 overflow-y-auto">
        {cards.length === 0 ? (
          <div className="text-xs text-[var(--text-disabled)] text-center py-8 border border-dashed border-[var(--border)] rounded-xl">
            Sin expedientes
          </div>
        ) : (
          cards.map((card) => <PipelineCard key={card.id} card={card} />)
        )}
      </div>
    </div>
  );
}
