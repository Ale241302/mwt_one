import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import RegisterCostDrawer from '@/components/modals/RegisterCostDrawer';
import api from '@/lib/api';

vi.mock('@/lib/api');
vi.mock('react-hot-toast', () => ({ default: { success: vi.fn(), error: vi.fn() } }));

const base = { open: true, onClose: vi.fn(), expedienteId: 'exp1', onSuccess: vi.fn() };

describe('RegisterCostDrawer', () => {
  it('renders drawer when open', () => {
    render(<RegisterCostDrawer {...base} />);
    expect(screen.getByText(/Registrar Costo/i)).toBeTruthy();
  });

  it('does not render when closed', () => {
    render(<RegisterCostDrawer {...base} open={false} />);
    expect(screen.queryByText(/Registrar Costo/i)).toBeNull();
  });

  it('has all required fields', () => {
    render(<RegisterCostDrawer {...base} />);
    expect(screen.getByText(/Tipo de costo/i)).toBeTruthy();
    expect(screen.getByText(/Monto/i)).toBeTruthy();
    expect(screen.getByText(/Moneda/i)).toBeTruthy();
    expect(screen.getByText(/Fase/i)).toBeTruthy();
  });

  it('calls C15 endpoint on submit', async () => {
    (api.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({});
    render(<RegisterCostDrawer {...base} />);
    // fill required fields
    fireEvent.change(screen.getAllByRole('combobox')[0], { target: { value: 'FLETE' } });
    fireEvent.change(screen.getByRole('spinbutton'), { target: { value: '500' } });
    fireEvent.change(screen.getAllByRole('combobox')[1], { target: { value: 'USD' } });
    fireEvent.change(screen.getAllByRole('combobox')[2], { target: { value: 'TRANSITO' } });
    fireEvent.click(screen.getByRole('button', { name: /Registrar/i }));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith(
      'expedientes/exp1/costs/', expect.any(Object)
    ));
  });

  it('visibility toggle defaults to internal', () => {
    render(<RegisterCostDrawer {...base} />);
    expect(screen.getByText(/Interno/i)).toBeTruthy();
  });
});
