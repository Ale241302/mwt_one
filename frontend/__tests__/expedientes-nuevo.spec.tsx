import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import api from '@/lib/api';

vi.mock('@/lib/api');
vi.mock('react-hot-toast', () => ({ default: { success: vi.fn(), error: vi.fn() } }));
vi.mock('next/navigation', () => ({ useRouter: () => ({ push: vi.fn() }) }));

// Dynamic import to avoid SSR issues
let NuevoExpedientePage: React.ComponentType;

beforeAll(async () => {
  const mod = await import('@/app/(mwt)/(dashboard)/expedientes/nuevo/page');
  NuevoExpedientePage = mod.default;
});

const mockClients = [
  { id: 'c1', name: 'Cliente A' },
  { id: 'c2', name: 'Cliente B' },
];

describe('NuevoExpedientePage', () => {
  beforeEach(() => {
    (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({ data: mockClients });
  });

  it('renders the new expediente form', async () => {
    render(<NuevoExpedientePage />);
    expect(screen.getByText(/Nuevo Expediente/i)).toBeTruthy();
  });

  it('loads clients in select', async () => {
    render(<NuevoExpedientePage />);
    await waitFor(() => expect(screen.getByText('Cliente A')).toBeTruthy());
  });

  it('all required enum selects present', async () => {
    render(<NuevoExpedientePage />);
    await waitFor(() => screen.getByText('Cliente A'));
    expect(screen.getByText(/SKECHERS/i)).toBeTruthy();
    expect(screen.getByText(/IMPORTACION/i)).toBeTruthy();
    expect(screen.getByText(/MARITIMO/i)).toBeTruthy();
  });

  it('shows error toast on API failure 400', async () => {
    (api.post as ReturnType<typeof vi.fn>).mockRejectedValueOnce({
      response: { data: { detail: 'Error de validación' } },
    });
    render(<NuevoExpedientePage />);
    await waitFor(() => screen.getByText('Cliente A'));
    // select client
    fireEvent.change(screen.getAllByRole('combobox')[0], { target: { value: 'c1' } });
    fireEvent.click(screen.getByRole('button', { name: /Crear Expediente/i }));
    await waitFor(() => {
      const { default: toast } = require('react-hot-toast');
      expect(toast.error).toHaveBeenCalled();
    });
  });
});
