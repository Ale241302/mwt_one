"use client";
import React from 'react';
import { ShoppingCart } from 'lucide-react';

export function OrdersTab() {
  return (
    <div className="card p-12 text-center text-text-tertiary">
      <ShoppingCart size={40} className="mx-auto mb-3 opacity-20" />
      <p className="text-sm font-semibold text-navy">Ordenes del Brand</p>
      <p className="text-xs mt-1">Vea los pedidos entrantes de sus clientes y su estado de ejecución.</p>
    </div>
  );
}
