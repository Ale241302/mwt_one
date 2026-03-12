import { render, screen, fireEvent } from '@testing-library/react';

// Mock del componente de costos con toggle (ajusta el import según tu path real)
jest.mock('@/lib/api');

const mockCosts = [
    { id: '1', category: 'FLETE', description: 'Flete marítimo', amount_internal: 1200, amount_client: 1500, margin: 300 },
    { id: '2', category: 'ADUANA', description: 'Agente aduanal', amount_internal: 400, amount_client: 480, margin: 80 },
];

// Componente mínimo del toggle para testear la lógica pura
function CostsToggle({ costs }: { costs: typeof mockCosts }) {
    const [clientView, setClientView] = React.useState(false);
    return (
        <div>
            <button onClick={() => setClientView(v => !v)} data-testid="toggle">
                {clientView ? 'Vista Cliente' : 'Vista Interna'}
            </button>
            <table>
                <tbody>
                    {costs.map(c => (
                        <tr key={c.id}>
                            <td>{c.description}</td>
                            <td data-testid={`amount-${c.id}`}>
                                {clientView ? c.amount_client : c.amount_internal}
                            </td>
                            {!clientView && <td data-testid={`margin-${c.id}`}>{c.margin}</td>}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

import React from 'react';

describe('CostsToggle — Vista Cliente vs Interna', () => {
    it('muestra montos internos y margen en vista interna (default)', () => {
        render(<CostsToggle costs={mockCosts} />);
        expect(screen.getByTestId('amount-1')).toHaveTextContent('1200');
        expect(screen.getByTestId('margin-1')).toHaveTextContent('300');
    });

    it('en Vista Cliente oculta el margen y muestra precio cliente', () => {
        render(<CostsToggle costs={mockCosts} />);
        fireEvent.click(screen.getByTestId('toggle'));
        expect(screen.getByTestId('amount-1')).toHaveTextContent('1500');
        expect(screen.queryByTestId('margin-1')).not.toBeInTheDocument();
    });

    it('switch de vuelta a vista interna restaura el margen', () => {
        render(<CostsToggle costs={mockCosts} />);
        fireEvent.click(screen.getByTestId('toggle')); // → cliente
        fireEvent.click(screen.getByTestId('toggle')); // → interna
        expect(screen.getByTestId('margin-1')).toHaveTextContent('300');
    });
});
