"use client";

import { useState } from "react";

interface Props {
  onSaved: () => void;
  onClose: () => void;
}

export function TemplateEditor({ onSaved, onClose }: Props) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-navy-dark p-6 rounded-xl w-full max-w-lg border border-[rgba(255,255,255,0.1)] shadow-2xl">
        <h2 className="text-xl font-bold text-white mb-4">Editar / Crear Template</h2>
        <p className="text-[rgba(255,255,255,0.6)] mb-6">Componente stub para la creación de Templates.</p>
        
        {/* Placeholder form for future MVP expansion */}
        <div className="space-y-4">
           {/* Fields would go here */}
           <div className="p-4 bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.05)] text-center text-sm text-[rgba(255,255,255,0.5)]">
             [ Formulario JSX de Template Editor ]
           </div>
        </div>

        <div className="mt-6 flex justify-end space-x-3">
          <button onClick={onClose} className="px-4 py-2 text-sm text-[rgba(255,255,255,0.7)] hover:text-white transition-colors border border-[rgba(255,255,255,0.1)] rounded">
            Cancelar
          </button>
          <button onClick={onSaved} className="px-4 py-2 text-sm bg-mint text-navy-dark font-bold rounded hover:bg-mint-hover transition-colors">
            Guardar
          </button>
        </div>
      </div>
    </div>
  );
}
