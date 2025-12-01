import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import UsedColumns from './UsedColumns';

describe('UsedColumns Component', () => {
  it('should display all used columns', () => {
    const columns = ['Product', 'Sales', 'Date'];

    render(<UsedColumns columns={columns} />);

    expect(screen.getByText('Product')).toBeInTheDocument();
    expect(screen.getByText('Sales')).toBeInTheDocument();
    expect(screen.getByText('Date')).toBeInTheDocument();
  });

  it('should handle empty columns array', () => {
    render(<UsedColumns columns={[]} />);
    expect(screen.getByText(/no columns used/i)).toBeInTheDocument();
  });

  it('should handle null columns', () => {
    render(<UsedColumns columns={null as any} />);
    expect(screen.getByText(/no columns used/i)).toBeInTheDocument();
  });
});

