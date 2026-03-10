import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import PipelineActionsPanel from '@/components/expediente/PipelineActionsPanel';
import api from '@/lib/api';

vi.mock('@/lib/api');
vi.mock('react-hot-toast', () => ({ default: { success: vi.fn(), error: vi.fn() } }));

const base = {
  expedienteId: 'exp1',
  availableActions: ['C6'],
  isBlocked: false,
  status: 'REGISTRO',
  onActionSuccess: vi.fn(),
};

describe('PipelineActionsPanel', () => {
  it('renders available action buttons', () => {
    render(<PipelineActionsPanel {...base} />);
    expect(screen.getByText(/Confirmar Producción|C6/i)).toBeTruthy();
  });

  it('shows BLOQUEADO badge when isBlocked=true', () => {
    render(<PipelineActionsPanel {...base} isBlocked={true} />);
    expect(screen.getByText(/BLOQUEADO/i)).toBeTruthy();
  });

  it('does not render when status=CANCELADO', () => {
    const { container } = render(<PipelineActionsPanel {...base} status="CANCELADO" />);
    expect(container.firstChild).toBeNull();
  });

  it('does not render when status=CERRADO', () => {
    const { container } = render(<PipelineActionsPanel {...base} status="CERRADO" />);
    expect(container.firstChild).toBeNull();
  });

  it('shows confirmation modal before executing action', () => {
    render(<PipelineActionsPanel {...base} />);
    fireEvent.click(screen.getByText(/Confirmar Producción|C6/i));
    expect(screen.getByText(/Confirmar acción|Confirmar/i)).toBeTruthy();
  });

  it('calls correct endpoint on confirm', async () => {
    (api.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({});
    render(<PipelineActionsPanel {...base} />);
    fireEvent.click(screen.getByText(/Confirmar Producción|C6/i));
    fireEvent.click(screen.getByRole('button', { name: /Confirmar/i }));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith(
      'expedientes/exp1/confirm-production/'
    ));
    expect(base.onActionSuccess).toHaveBeenCalled();
  });
});
