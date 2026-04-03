"use client";
import React from 'react';
import { FileText } from 'lucide-react';

export function AgreementsTab() {
  return (
    <div className="card p-12 text-center text-text-tertiary">
      <FileText size={40} className="mx-auto mb-3 opacity-20" />
      <p className="text-sm font-semibold text-navy">Agreements & Polizas de Assortment</p>
      <p className="text-xs mt-1">Gestione sus acuerdos de nivel de servicio y políticas por cliente.</p>
    </div>
  );
}
