import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import ArtifactFormDrawer from '@/components/modals/ArtifactFormDrawer';

vi.mock('@/lib/api');
vi.mock('react-hot-toast', () => ({ default: { success: vi.fn(), error: vi.fn() } }));

const baseProps = {
  open: true,
  onClose: vi.fn(),
  expedienteId: 'exp1',
  expedienteMode: 'IMPORTACION',
  freightMode: 'MARITIMO',
  dispatchMode: 'mwt',
  artifacts: [],
  onSuccess: vi.fn(),
};

describe('ArtifactFormDrawer - ART-02 comision field', () => {
  it('hides comision_pactada when mode != COMISION', () => {
    render(<ArtifactFormDrawer {...baseProps} artifactType="ART-02" />);
    expect(screen.queryByText(/Comisión pactada/i)).toBeNull();
  });

  it('shows comision_pactada when mode = COMISION', () => {
    render(<ArtifactFormDrawer {...baseProps} artifactType="ART-02" expedienteMode="COMISION" />);
    expect(screen.getByText(/Comisión pactada/i)).toBeTruthy();
  });
});

describe('ArtifactFormDrawer - ART-05 dynamic label', () => {
  it('shows AWB Number for AEREO', () => {
    render(<ArtifactFormDrawer {...baseProps} artifactType="ART-05" freightMode="AEREO" />);
    expect(screen.getByText(/AWB Number/i)).toBeTruthy();
  });

  it('shows BL Number for MARITIMO', () => {
    render(<ArtifactFormDrawer {...baseProps} artifactType="ART-05" freightMode="MARITIMO" />);
    expect(screen.getByText(/BL Number/i)).toBeTruthy();
  });
});

describe('ArtifactFormDrawer - ART-07 precondition', () => {
  it('shows blocked warning when ART-05 and ART-06 not completed', () => {
    render(<ArtifactFormDrawer {...baseProps} artifactType="ART-07" artifacts={[]} />);
    expect(screen.getByText(/Requiere ART-05 y ART-06/i)).toBeTruthy();
  });

  it('submit button disabled when ART-07 blocked', () => {
    render(<ArtifactFormDrawer {...baseProps} artifactType="ART-07" artifacts={[]} />);
    const btn = screen.getByRole('button', { name: /Registrar Artefacto/i });
    expect(btn).toBeDisabled();
  });

  it('enables ART-07 when ART-05 and ART-06 completed', () => {
    const arts = [
      { artifact_type: 'ART-05', status: 'COMPLETED' },
      { artifact_type: 'ART-06', status: 'COMPLETED' },
    ];
    render(<ArtifactFormDrawer {...baseProps} artifactType="ART-07" artifacts={arts} />);
    expect(screen.queryByText(/Requiere ART-05 y ART-06/i)).toBeNull();
  });
});

describe('ArtifactFormDrawer - ART-08 dispatch mode', () => {
  it('renders ART-08 when dispatchMode=mwt', () => {
    render(<ArtifactFormDrawer {...baseProps} artifactType="ART-08" dispatchMode="mwt" />);
    expect(screen.getByText(/Agente aduanal/i)).toBeTruthy();
  });
});
