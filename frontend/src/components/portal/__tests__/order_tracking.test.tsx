import React from 'react';
import { render, screen } from '@testing-library/react';
import { StateTimelinePortal } from '../StateTimelinePortal';

// Mock dependencies
jest.mock('@/lib/constants/states', () => ({
  STATE_LABELS: { REGISTRO: 'Registro', TRANSITO: 'Tránsito', EN_DESTINO: 'En destino' },
  TIMELINE_STEPS: ['REGISTRO', 'TRANSITO', 'EN_DESTINO']
}));

describe('StateTimelinePortal Component', () => {
  it('renders timeline with current status correctly', () => {
    render(<StateTimelinePortal currentStatus="TRANSITO" />);
    expect(screen.getByText('Tránsito')).toBeInTheDocument();
    expect(screen.getByText('En destino')).toBeInTheDocument();
  });

  it('handles unknown status gracefully by placing at index 0', () => {
    render(<StateTimelinePortal currentStatus="UNKNOWN" />);
    expect(screen.getByText('Progreso del Expediente')).toBeInTheDocument();
  });
});
