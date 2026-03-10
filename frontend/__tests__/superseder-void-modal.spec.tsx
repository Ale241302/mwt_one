import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import SupersederModal from '@/components/modals/SupersederModal';
import VoidArtifactModal from '@/components/modals/VoidArtifactModal';
import api from '@/lib/api';

vi.mock('@/lib/api');
vi.mock('react-hot-toast', () => ({ default: { success: vi.fn(), error: vi.fn() } }));

describe('SupersederModal', () => {
  const props = {
    open: true, onClose: vi.fn(), expedienteId: 'exp1',
    artifactId: 'art123', artifactType: 'ART-01', onSuccess: vi.fn(),
  };

  it('renders superseder warning', () => {
    render(<SupersederModal {...props} />);
    expect(screen.getByText(/SUPERSEDED/)).toBeTruthy();
  });

  it('calls supersede endpoint on confirm', async () => {
    (api.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({});
    render(<SupersederModal {...props} />);
    fireEvent.click(screen.getByRole('button', { name: /Confirmar Superseder/i }));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith(
      'expedientes/exp1/artifacts/art123/supersede/'
    ));
    expect(props.onSuccess).toHaveBeenCalled();
  });
});

describe('VoidArtifactModal', () => {
  const props = {
    open: true, onClose: vi.fn(), expedienteId: 'exp1', onSuccess: vi.fn(),
  };

  it('renders strong warning about pipeline consequences', () => {
    render(<VoidArtifactModal {...props} />);
    expect(screen.getByText(/consecuencias en el pipeline/i)).toBeTruthy();
  });

  it('submit button disabled when reason < 15 chars', () => {
    render(<VoidArtifactModal {...props} />);
    fireEvent.change(screen.getByPlaceholderText(/motivo/i), { target: { value: 'corto' } });
    expect(screen.getByRole('button', { name: /Anular Factura/i })).toBeDisabled();
  });

  it('calls void-artifact endpoint with ART-09', async () => {
    (api.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({});
    render(<VoidArtifactModal {...props} />);
    fireEvent.change(screen.getByPlaceholderText(/motivo/i), {
      target: { value: 'Razón válida con más de quince chars' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Anular Factura/i }));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith(
      'expedientes/exp1/void-artifact/',
      expect.objectContaining({ artifact_type: 'ART-09' })
    ));
  });
});
