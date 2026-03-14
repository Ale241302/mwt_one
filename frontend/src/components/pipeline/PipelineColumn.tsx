"use client";
import { CanonicalState } from "@/lib/constants/states";
import { ExpedienteCard } from "./PipelineView";
import { PipelineCard } from "./PipelineCard";
import { Inbox } from "lucide-react";

interface PipelineColumnProps {
  state: CanonicalState;
  label: string;
  cards: ExpedienteCard[];
}

export function PipelineColumn({ state: _state, label, cards }: PipelineColumnProps) {
  return (
    <div className="flex flex-col w-64 min-w-[256px]">
      {/* ── Column header ── */}
      <div className="flex items-center justify-between mb-2 px-1">
        <span className="text-xs font-semibold uppercase tracking-[0.5px] text-[var(--text-tertiary)]">
          {label}
        </span>
        <span
          className={cn(
            "text-xs px-1.5 py-0.5 rounded-full font-medium",
            cards.length > 0
              ? "bg-[var(--navy)] text-[var(--text-inverse)]"
              : "bg-[var(--bg-alt)] text-[var(--text-disabled)]"
          )}
        >
          {cards.length}
        </span>
      </div>

      {/* ── Cards ── */}
      <div className="flex flex-col gap-2 flex-1 overflow-y-auto">
        {cards.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-1.5 py-8 border border-dashed border-[var(--border)] rounded-xl text-[var(--text-disabled)]">
            <Inbox size={16} aria-hidden />
            <span className="text-xs">Sin expedientes</span>
          </div>
        ) : (
          cards.map((card) => <PipelineCard key={card.id} card={card} />)
        )}
      </div>
    </div>
  );
}

function cn(...classes: (string | false | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}
