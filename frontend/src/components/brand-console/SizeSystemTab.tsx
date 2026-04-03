"use client";
import React from 'react';
import { Ruler } from 'lucide-react';

export function SizeSystemTab() {
  return (
    <div className="card p-12 text-center text-text-tertiary">
      <Ruler size={40} className="mx-auto mb-3 opacity-20" />
      <p className="text-sm font-semibold text-navy">Sistema de Tallas</p>
      <p className="text-xs mt-1">Configuración del BrandSizeSystem y mapeos de tallas por referencia.</p>
    </div>
  );
}
