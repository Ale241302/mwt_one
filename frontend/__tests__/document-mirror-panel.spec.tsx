import { render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import DocumentMirrorPanel from '@/components/expediente/DocumentMirrorPanel';
import api from '@/lib/api';

vi.mock('@/lib/api');
vi.mock('date-fns', () => ({ format: () => '10 mar 2026' }));
vi.mock('date-fns/locale', () => ({ es: {} }));

describe('DocumentMirrorPanel', () => {
  it('shows empty state when no documents', async () => {
    (api.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({ data: [] });
    render(<DocumentMirrorPanel expedienteId="exp1" />);
    await waitFor(() => expect(screen.getByText(/No hay documentos/i)).toBeTruthy());
  });

  it('renders documents with links', async () => {
    (api.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: [
        { id: '1', name: 'Factura.pdf', file_url: 'https://example.com/doc1.pdf', created_at: '2026-03-10', artifact_type: 'ART-09' },
        { id: '2', name: 'BL.pdf', file_url: 'https://example.com/doc2.pdf', created_at: '2026-03-09', artifact_type: 'ART-05' },
      ],
    });
    render(<DocumentMirrorPanel expedienteId="exp1" />);
    await waitFor(() => expect(screen.getByText('Factura.pdf')).toBeTruthy());
    expect(screen.getByText('BL.pdf')).toBeTruthy();
  });

  it('document links open in new tab', async () => {
    (api.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: [{ id: '1', name: 'Doc.pdf', file_url: 'https://example.com/doc.pdf', created_at: '2026-03-10' }],
    });
    render(<DocumentMirrorPanel expedienteId="exp1" />);
    await waitFor(() => screen.getByText('Doc.pdf'));
    const link = screen.getByTitle('Ver documento').closest('a');
    expect(link?.getAttribute('target')).toBe('_blank');
    expect(link?.getAttribute('href')).toBe('https://example.com/doc.pdf');
  });

  it('shows badge count when documents loaded', async () => {
    (api.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      data: [
        { id: '1', name: 'A.pdf', file_url: 'https://x.com/a.pdf', created_at: '2026-03-10' },
      ],
    });
    render(<DocumentMirrorPanel expedienteId="exp1" />);
    await waitFor(() => expect(screen.getByText('1')).toBeTruthy());
  });
});
