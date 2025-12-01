import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import ResultTable from './ResultTable';

describe('ResultTable Component', () => {
  it('should display table with correct data', () => {
    const result = [
      { Product: 'A', Sales: 100 },
      { Product: 'B', Sales: 200 }
    ];
    const columns = ['Product', 'Sales'];

    render(<ResultTable result={result} columns={columns} />);

    // Check headers
    expect(screen.getByText('Product')).toBeInTheDocument();
    expect(screen.getByText('Sales')).toBeInTheDocument();

    // Check data
    expect(screen.getByText('A')).toBeInTheDocument();
    expect(screen.getByText('100')).toBeInTheDocument();
    expect(screen.getByText('B')).toBeInTheDocument();
    expect(screen.getByText('200')).toBeInTheDocument();
  });

  it('should handle empty result', () => {
    render(<ResultTable result={[]} columns={[]} />);
    expect(screen.getByText(/no results to display/i)).toBeInTheDocument();
  });

  it('should handle null result', () => {
    render(<ResultTable result={null} columns={null} />);
    expect(screen.getByText(/no results to display/i)).toBeInTheDocument();
  });

  it('should infer columns from result if not provided', () => {
    const result = [
      { Product: 'A', Sales: 100 },
      { Product: 'B', Sales: 200 }
    ];

    render(<ResultTable result={result} columns={null} />);

    expect(screen.getByText('Product')).toBeInTheDocument();
    expect(screen.getByText('Sales')).toBeInTheDocument();
  });
});

