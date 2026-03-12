import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import RegisterPaymentDrawer from '@/components/RegisterPaymentDrawer';
import api from '@/lib/api';

jest.mock('@/lib/api');
jest.mock('react-hot-toast', () => ({ error: jest.fn(), success: jest.fn() }));

const defaultProps = {
  open: true,
  onClose: jest.fn(),
  expedienteId: 'exp-001',
  expedienteCurrency: 'USD',
  financialSummary: {
    total_billed_client: 5000,
    total_paid: 2000,
    balance_pending: 3000,
    payment_status: 'PARTIAL',
  },
  onSuccess: jest.fn(),
};

describe('RegisterPaymentDrawer', () => {
  beforeEach(() => jest.clearAllMocks());

  it('renderiza el resumen financiero correctamente', () => {
    render(<RegisterPaymentDrawer {...defaultProps} />);
    expect(screen.getByText(/Total Facturado/i)).toBeInTheDocument();
    expect(screen.getByText(/\$5,000\.00/i)).toBeInTheDocument();
    expect(screen.getByText(/PARTIAL/i)).toBeInTheDocument();
  });

  it('no renderiza nada cuando open=false', () => {
    render(<RegisterPaymentDrawer {...defaultProps} open={false} />);
    expect(screen.queryByText(/Registrar Pago/i)).not.toBeInTheDocument();
  });

  it('muestra advertencia si moneda difiere del expediente', () => {
    render(<RegisterPaymentDrawer {...defaultProps} />);
    const currencySelect = screen.getByDisplayValue('USD');
    fireEvent.change(currencySelect, { target: { name: 'currency', value: 'COP' } });
    expect(screen.getByText(/Difiere del expediente/i)).toBeInTheDocument();
  });

  it('valida campos requeridos antes de submit', async () => {
    const toast = require('react-hot-toast');
    render(<RegisterPaymentDrawer {...defaultProps} />);
    fireEvent.click(screen.getByText('Registrar Pago'));
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Completa todos los campos obligatorios');
    });
    expect(api.post).not.toHaveBeenCalled();
  });

  it('envía el pago correctamente con datos válidos', async () => {
    (api.post as jest.Mock).mockResolvedValueOnce({});
    render(<RegisterPaymentDrawer {...defaultProps} />);

    fireEvent.change(screen.getByPlaceholderText('0.00'), {
      target: { name: 'amount', value: '1000' },
    });
    fireEvent.change(screen.getByDisplayValue('Seleccionar...'), {
      target: { name: 'method', value: 'TRANSFERENCIA' },
    });

    fireEvent.click(screen.getByText('Registrar Pago'));
    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith(
        'expedientes/exp-001/register-payment/',
        expect.objectContaining({ amount: 1000, method: 'TRANSFERENCIA' })
      );
      expect(defaultProps.onSuccess).toHaveBeenCalled();
      expect(defaultProps.onClose).toHaveBeenCalled();
    });
  });

  it('muestra error de API si el registro falla', async () => {
    const toast = require('react-hot-toast');
    (api.post as jest.Mock).mockRejectedValueOnce({
      response: { data: { detail: 'Saldo insuficiente' } },
    });
    render(<RegisterPaymentDrawer {...defaultProps} />);

    fireEvent.change(screen.getByPlaceholderText('0.00'), {
      target: { name: 'amount', value: '9999' },
    });
    fireEvent.change(screen.getByDisplayValue('Seleccionar...'), {
      target: { name: 'method', value: 'EFECTIVO' },
    });
    fireEvent.click(screen.getByText('Registrar Pago'));
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Saldo insuficiente');
    });
  });
});
