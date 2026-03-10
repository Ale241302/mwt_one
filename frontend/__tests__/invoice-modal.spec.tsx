import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import InvoiceModal from '@/components/modals/InvoiceModal';
import api from '@/lib/api';

vi.mock('@/lib/api');
vi.mock('react-hot-toast', () => ({ default: { success: vi.fn(), error: vi.fn() } }));
vi.mock('date-fns', () => ({ format: () => '2026-03-10' }));

const art01Completed = { artifact_type: 'ART-01', status: 'COMPLETED' };
const art02Completed = {
  artifact_type: 'ART-02', status: 'COMPLETED',
  payload: { total_amount: 5000, currency: 'USD', incoterm: 'FOB' },
};

const baseProps = {
  open: true,
  onClose: vi.fn(),
  expedienteId: 'exp1',
  clientName: 'Cliente Test S.A.',
  expedienteMode: 'IMPORTACION',
  dispatchMode: 'mwt',
  artifacts: [art01Completed, art02Completed],
  onSuccess: vi.fn(),
};

describe('InvoiceModal', () => {
  it('renders modal with preview data', () => {
    render(<InvoiceModal {...baseProps} />);
    expect(screen.getByText('Cliente Test S.A.')).toBeTruthy();
    expect(screen.getByText(/5.000/)).toBeTruthy();
  });

  it('shows IVA field when dispatchMode=mwt', () => {
    render(<InvoiceModal {...baseProps} />);
    expect(screen.getByText(/IVA/i)).toBeTruthy();
  });

  it('hides IVA field when dispatchMode=directo', () => {
    render(<InvoiceModal {...baseProps} dispatchMode="directo" />);
    expect(screen.queryByText(/IVA/i)).toBeNull();
  });

  it('submit disabled without invoice number', () => {
    render(<InvoiceModal {...baseProps} />);
    const btn = screen.getByRole('button', { name: /Emitir Factura/i });
    expect(btn).toBeDisabled();
  });

  it('submits with invoice number', async () => {
    (api.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({});
    render(<InvoiceModal {...baseProps} />);
    fireEvent.change(screen.getByPlaceholderText(/MWT-2026/i), {
      target: { value: 'MWT-2026-001' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Emitir Factura/i }));
    await waitFor(() => expect(baseProps.onSuccess).toHaveBeenCalled());
  });

  it('shows comision when mode=COMISION', () => {
    const arts = [art01Completed, {
      ...art02Completed,
      payload: { ...art02Completed.payload, comision_pactada: 5 },
    }];
    render(<InvoiceModal {...baseProps} expedienteMode="COMISION" artifacts={arts} />);
    expect(screen.getByText(/Comisión pactada/i)).toBeTruthy();
  });
});
