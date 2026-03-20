"use client";
import React from "react";
import { CheckCircle, AlertTriangle, ArrowRight } from "lucide-react";

interface GateMessageProps {
  requiredToAdvance: string[];
  currentState: string;
}

export default function GateMessage({ requiredToAdvance, currentState }: GateMessageProps) {
  if (currentState === "CERRADO" || currentState === "CANCELADO") {
    return null; // No advancement in terminal states
  }

  const isReady = requiredToAdvance.length === 0;

  if (isReady) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-start gap-3">
        <CheckCircle className="text-green-700 shrink-0 mt-0.5" size={18} />
        <div>
          <h4 className="text-sm font-semibold text-green-700 mb-1">
            Listo para avanzar
          </h4>
          <p className="text-xs text-green-700/80">
            Todos los requisitos de la fase actual están completos.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-start gap-3">
      <AlertTriangle className="text-amber-700 shrink-0 mt-0.5" size={18} />
      <div>
        <h4 className="text-sm font-semibold text-amber-700 mb-1">
          Requisitos para avanzar
        </h4>
        <ul className="text-xs text-amber-700/80 space-y-1 mt-2">
          {(Array.isArray(requiredToAdvance) ? requiredToAdvance : []).map((req, i) => (
            <li key={i} className="flex items-center gap-2">
              <ArrowRight size={10} /> {req}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
