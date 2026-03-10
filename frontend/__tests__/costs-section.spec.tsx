import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import CostsSection from '@/components/expediente/CostsSection';
import api from '@/lib/api';

vi.mock('@/lib/api');

const mockCosts = [
  { id: '1', cost_type: 'FLETE', description: 'Flete mar', phase: 'TRANSITO', amount: 1000, currency: 'USD', visibility: 'internal' },
  { id: '2', cost_type: 'ADUANA', description: 'Tasa', phase: 'DESTINO', amount: 200, currency: 'USD', visibility: 'client' },
];

const mockSummary = {
  total_billed_client: 0,
  total_costs: 1200,
  total_paid: 0,
  payment_status: 'PENDING',
  has_invoice: false,
};

beforeEach(() => {
  (api.get as ReturnType<typeof vi.fn>)
    .mockImplementation((url: string) => {
      if (url.includes('costs')) return Promise.resolve({ data: mockCosts });
      if (url.includes('financial-summary')) return Promise.resolve({ data: mockSummary });
      return Promise.resolve({ data: [] });
    });
});

describe('CostsSection', () => {
  it('renders section with costs', async () => {
    render(<CostsSection expedienteId="exp1" onRegisterCost={vi.fn()} />);
    await waitFor(() => expect(screen.getByText('FLETE')).toBeTruthy());
  });

  it('shows n/a margin when no invoice', async () => {
    render(<CostsSection expedienteId="exp1" onRegisterCost={vi.fn()} />);
    await waitFor(() => expect(screen.getByText(/n\/a/i)).toBeTruthy());
  });

  it('toggle switches to client view showing only client costs', async () => {
    render(<CostsSection expedienteId="exp1" onRegisterCost={vi.fn()} />);
    await waitFor(() => screen.getByText('FLETE'));
    fireEvent.click(screen.getByText('Vista Cliente'));
    expect(screen.getByText('ADUANA')).toBeTruthy();
    // internal-only cost not visible
    expect(screen.queryByText(/Margen bruto/i)).toBeNull();
  });

  it('calls onRegisterCost on button click', async () => {
    const mockFn = vi.fn();
    render(<CostsSection expedienteId="exp1" onRegisterCost={mockFn} />);
    await waitFor(() => screen.getByText(/Registrar Costo/i));
    fireEvent.click(screen.getByText(/Registrar Costo/i));
    expect(mockFn).toHaveBeenCalled();
  });
});
