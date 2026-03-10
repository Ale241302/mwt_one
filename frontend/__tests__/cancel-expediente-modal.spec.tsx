import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import CancelExpedienteModal from '@/components/modals/CancelExpedienteModal';
import api from '@/lib/api';

vi.mock('@/lib/api');
vi.mock('react-hot-toast', () => ({ default: { success: vi.fn(), error: vi.fn() } }));

const base = { open: true, onClose: vi.fn(), expedienteId: 'exp1', onSuccess: vi.fn() };

describe('CancelExpedienteModal', () => {
  it('renders modal when open', () => {
    render(<CancelExpedienteModal {...base} />);
    expect(screen.getByText(/Cancelar Expediente/i)).toBeTruthy();
  });

  it('shows irreversible warning banner', () => {
    render(<CancelExpedienteModal {...base} />);
    expect(screen.getByText(/acción es irreversible/i)).toBeTruthy();
  });

  it('submit button disabled when reason < 20 chars', () => {
    render(<CancelExpedienteModal {...base} />);
    const textarea = screen.getByPlaceholderText(/motivo/i);
    fireEvent.change(textarea, { target: { value: 'corto' } });
    const btn = screen.getByRole('button', { name: /Cancelar Expediente/i });
    expect(btn).toBeDisabled();
  });

  it('submit enabled when reason >= 20 chars', () => {
    render(<CancelExpedienteModal {...base} />);
    const textarea = screen.getByPlaceholderText(/motivo/i);
    fireEvent.change(textarea, { target: { value: 'Razón con más de veinte caracteres valida' } });
    const btn = screen.getByRole('button', { name: /Cancelar Expediente/i });
    expect(btn).not.toBeDisabled();
  });

  it('calls cancel API and onSuccess on submit', async () => {
    (api.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({});
    render(<CancelExpedienteModal {...base} />);
    fireEvent.change(screen.getByPlaceholderText(/motivo/i), {
      target: { value: 'Razón con más de veinte caracteres valida' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Cancelar Expediente/i }));
    await waitFor(() => expect(base.onSuccess).toHaveBeenCalled());
    expect(api.post).toHaveBeenCalledWith('expedientes/exp1/cancel/', expect.any(Object));
  });

  it('does not render when open=false', () => {
    render(<CancelExpedienteModal {...base} open={false} />);
    expect(screen.queryByText(/Cancelar Expediente/i)).toBeNull();
  });
});
