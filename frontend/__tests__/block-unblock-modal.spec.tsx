import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import BlockUnblockModal from '@/components/modals/BlockUnblockModal';
import api from '@/lib/api';

vi.mock('@/lib/api');
vi.mock('react-hot-toast', () => ({ default: { success: vi.fn(), error: vi.fn() } }));

describe('BlockUnblockModal - Block mode', () => {
  const props = {
    open: true, onClose: vi.fn(), expedienteId: 'exp1',
    isBlocked: false, onSuccess: vi.fn(),
  };

  it('renders block form', () => {
    render(<BlockUnblockModal {...props} />);
    expect(screen.getByText(/Bloquear Expediente/i)).toBeTruthy();
  });

  it('submit disabled when reason < 10 chars', () => {
    render(<BlockUnblockModal {...props} />);
    fireEvent.change(screen.getByPlaceholderText(/razón/i), { target: { value: 'corto' } });
    expect(screen.getByRole('button', { name: /Bloquear Expediente/i })).toBeDisabled();
  });

  it('calls block endpoint on submit', async () => {
    (api.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({});
    render(<BlockUnblockModal {...props} />);
    fireEvent.change(screen.getByPlaceholderText(/razón/i), {
      target: { value: 'Razón válida de más de 10 chars' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Bloquear Expediente/i }));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith(
      'expedientes/exp1/block/',
      expect.objectContaining({ blocked_by_type: 'CEO' })
    ));
  });
});

describe('BlockUnblockModal - Unblock mode', () => {
  const props = {
    open: true, onClose: vi.fn(), expedienteId: 'exp1',
    isBlocked: true, blockReason: 'Bloqueado por CEO', blockedByType: 'CEO', onSuccess: vi.fn(),
  };

  it('shows current block reason', () => {
    render(<BlockUnblockModal {...props} />);
    expect(screen.getByText('Bloqueado por CEO')).toBeTruthy();
  });

  it('shows unblock button (not block)', () => {
    render(<BlockUnblockModal {...props} />);
    expect(screen.getByRole('button', { name: /Desbloquear/i })).toBeTruthy();
    expect(screen.queryByRole('button', { name: /Bloquear Expediente/i })).toBeNull();
  });
});

describe('BlockUnblockModal - SYSTEM block', () => {
  const props = {
    open: true, onClose: vi.fn(), expedienteId: 'exp1',
    isBlocked: true, blockReason: 'Auto: crédito vencido', blockedByType: 'SYSTEM', onSuccess: vi.fn(),
  };

  it('does not show unblock button for SYSTEM block', () => {
    render(<BlockUnblockModal {...props} />);
    expect(screen.queryByRole('button', { name: /Desbloquear/i })).toBeNull();
  });

  it('shows system message', () => {
    render(<BlockUnblockModal {...props} />);
    expect(screen.getByText(/bloqueado automáticamente/i)).toBeTruthy();
  });
});
