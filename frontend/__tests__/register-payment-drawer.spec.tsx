import { render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import RegisterPaymentDrawer from '@/components/modals/RegisterPaymentDrawer';
import api from '@/lib/api';

vi.mock('@/lib/api');
vi.mock('react-hot-toast', () => ({ default: { success: vi.fn(), error: vi.fn() } }));

const mockSummary = {
  total_billed_client: 5000,
  total_paid: 1000,
  payment_status: 'PARTIAL',
};

const base = {
  open: true, onClose: vi.fn(), expedienteId: 'exp1',
  expedienteCurrency: 'USD', onSuccess: vi.fn(),
};

beforeEach(() => {
  (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: mockSummary });
});

describe('RegisterPaymentDrawer', () => {
  it('fetches financial summary on open', async () => {
    render(<RegisterPaymentDrawer {...base} />);
    await waitFor(() => expect(api.get).toHaveBeenCalledWith(
      'expedientes/exp1/financial-summary/'
    ));
  });

  it('displays total billed and paid', async () => {
    render(<RegisterPaymentDrawer {...base} />);
    await waitFor(() => expect(screen.getByText(/5.000|5,000/)).toBeTruthy());
  });

  it('has all required payment fields', async () => {
    render(<RegisterPaymentDrawer {...base} />);
    await waitFor(() => screen.getByText(/Monto/i));
    expect(screen.getByText(/Método/i)).toBeTruthy();
    expect(screen.getByText(/Referencia/i)).toBeTruthy();
    expect(screen.getByText(/Fecha de pago/i)).toBeTruthy();
  });

  it('does not render when closed', () => {
    render(<RegisterPaymentDrawer {...base} open={false} />);
    expect(screen.queryByText(/Registrar Pago/i)).toBeNull();
  });
});
