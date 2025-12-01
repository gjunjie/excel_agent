import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import CodeBlock from './CodeBlock';

describe('CodeBlock Component', () => {
  it('should display code correctly', () => {
    const code = 'import pandas as pd\nresult = df.sum()';

    render(<CodeBlock code={code} />);

    expect(screen.getByText(/import pandas/i)).toBeInTheDocument();
    expect(screen.getByText(/result = df.sum/i)).toBeInTheDocument();
  });

  it('should handle empty code', () => {
    render(<CodeBlock code="" />);
    const codeElement = screen.getByRole('code');
    expect(codeElement).toBeInTheDocument();
  });
});

