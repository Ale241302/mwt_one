"use client";
import React from 'react';
import { Layers } from 'lucide-react';

export function OverviewTab() {
  return (
    <div className="card p-12 text-center text-text-tertiary">
      <Layers size={40} className="mx-auto mb-3 opacity-20" />
      <p className="text-sm font-semibold text-navy">Brand Overview</p>
      <p className="text-xs mt-1">Métricas generales y alertas recientes aparecerán aquí.</p>
    </div>
  );
}
