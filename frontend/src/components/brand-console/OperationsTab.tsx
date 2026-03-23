import React from 'react';
import { STATE_LABELS } from '@/lib/constants/states';

export function OperationsTab() {
  const requirements = ['Documentación', 'Aprobación CEO', 'Pago Inicial', 'Revisión Aduana'];
  const states = Object.entries(STATE_LABELS);

  return (
    <div className="table-container">
      <div className="p-4" style={{ borderBottom: '1px solid var(--divider)' }}>
        <h2 className="heading-lg">Matriz de Operaciones y Requirements</h2>
      </div>
      <table>
        <thead>
          <tr>
            <th>Estado</th>
            {requirements.map(req => (
              <th key={req} style={{ textAlign: 'center' }}>{req}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {states.map(([key, label], idx) => (
            <tr key={key}>
              <td className="font-medium">{label}</td>
              {requirements.map((req, rIdx) => (
                <td key={`${key}-${req}`} style={{ textAlign: 'center' }}>
                  <input type="checkbox" defaultChecked={(idx + rIdx) % 3 === 0} />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
