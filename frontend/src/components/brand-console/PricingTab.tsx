import React, { useState } from 'react';
import { Reorder } from 'framer-motion';

export function PricingTab() {
  const [items, setItems] = useState([
    { id: '1', name: 'Standard Product A', price: 100 },
    { id: '2', name: 'Premium Product B', price: 250 },
    { id: '3', name: 'Enterprise Product C', price: 900 },
  ]);
  const [page, setPage] = useState(1);

  return (
    <div className="card p-6">
      <h2 className="heading-lg mb-4">Pricelists (Drag & Drop)</h2>
      <Reorder.Group axis="y" values={items} onReorder={setItems} className="flex flex-col gap-2">
        {items.map((item) => (
          <Reorder.Item 
            key={item.id} 
            value={item} 
            className="flex justify-between items-center p-4 rounded-lg cursor-grab active:cursor-grabbing"
            style={{ background: 'var(--bg-alt)', border: '1px solid var(--border)' }}
          >
            <span className="body-md font-medium">{item.name}</span>
            <span className="mono-md">${item.price}</span>
          </Reorder.Item>
        ))}
      </Reorder.Group>
      
      <div className="flex justify-between items-center mt-6 pt-4" style={{ borderTop: '1px solid var(--divider)' }}>
        <button 
          className="btn btn-sm btn-secondary" 
          disabled={page === 1} 
          onClick={() => setPage(p => p - 1)}
        >
          Anterior
        </button>
        <span className="caption">Página {page} de 5</span>
        <button 
          className="btn btn-sm btn-secondary" 
          onClick={() => setPage(p => p + 1)}
        >
          Siguiente
        </button>
      </div>
    </div>
  );
}
