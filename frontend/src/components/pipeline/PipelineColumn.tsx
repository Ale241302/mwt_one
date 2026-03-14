"use client";
import { PipelineCard } from "./PipelineCard";
import { ExpedienteCard } from "./PipelineView";

interface PipelineColumnProps {
  state: string;
  label: string;
  cards: ExpedienteCard[];
}

export function PipelineColumn({ label, cards }: PipelineColumnProps) {
  return (
    <div
      className="flex flex-col w-64 min-w-[256px] rounded-xl p-3 gap-2"
      style={{ background: "#F0F2F5", minHeight: "200px" }}
    >
      {/* Column header */}
      <div className="flex items-center justify-between mb-1 px-1">
        <span className="text-xs font-bold uppercase tracking-wider" style={{ color: "#3D4F5C" }}>
          {label}
        </span>
        <span
          className="text-[10px] font-bold w-5 h-5 rounded-full flex items-center justify-center"
          style={{ background: "#013A57", color: "#FFFFFF" }}
        >
          {cards.length}
        </span>
      </div>

      {/* Cards */}
      {cards.length === 0 ? (
        <div
          className="flex-1 flex items-center justify-center rounded-lg text-xs"
          style={{ border: "2px dashed #E2E5EA", color: "#B0BAC4", minHeight: "80px" }}
        >
          Sin expedientes
        </div>
      ) : (
        cards.map((card) => <PipelineCard key={card.id} card={card} />)
      )}
    </div>
  );
}
