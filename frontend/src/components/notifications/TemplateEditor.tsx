"use client";

import { useState } from "react";

interface Props {
  onSaved: () => void;
  onClose: () => void;
}

export function TemplateEditor({ onSaved, onClose }: Props) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-surface p-6 rounded-xl w-full max-w-lg border border-border shadow-2xl">
        <h2 className="text-xl font-bold text-text-primary mb-4">Editar / Crear Template</h2>
        <p className="text-text-secondary mb-6">Componente stub para la creación de Templates.</p>
        
        {/* Placeholder form for future MVP expansion */}
        <div className="space-y-4">
           {/* Fields would go here */}
           <div className="p-4 bg-bg-alt/30 border border-border text-center text-sm text-text-tertiary">
             [ Formulario JSX de Template Editor ]
           </div>
        </div>

        <div className="mt-6 flex justify-end space-x-3">
          <button onClick={onClose} className="px-4 py-2 text-sm text-text-secondary hover:text-text-primary transition-colors border border-border rounded">
            Cancelar
          </button>
          <button onClick={onSaved} className="px-4 py-2 text-sm bg-navy text-white font-bold rounded hover:bg-slate-800 transition-colors">
            Guardar
          </button>
        </div>
      </div>
    </div>
  );
}
