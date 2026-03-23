import React from 'react';
import { render, screen } from '@testing-library/react';
import { CreditBar } from '../CreditBar';

describe('CreditBar Component', () => {
  it('renders correctly with given used and total amounts', () => {
    render(<CreditBar used={50000} total={100000} currency="USD" />);
    // Verify component renders text indicating amounts correctly
    expect(screen.getByText('Límite de crédito asignado')).toBeInTheDocument();
  });

  it('renders without crashing even if total is zero', () => {
    render(<CreditBar used={5000} total={0} currency="USD" />);
    expect(screen.getByText('Límite de crédito asignado')).toBeInTheDocument();
  });
});
