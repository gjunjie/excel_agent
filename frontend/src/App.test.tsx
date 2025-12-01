/**
 * Comprehensive test suite for the Excel AI Agent frontend.
 * 
 * Tests cover:
 * 1. Text input → Analyze
 * 2. Correct Excel file selected
 * 3. Gemini intent JSON correct
 * 4. Python code auto-generated
 * 5. Code executes successfully
 * 6. Table displayed in UI
 * 7. Used columns displayed
 * 8. Error handling (bad question)
 * 9. Multiple Excel files
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import App from './App';

// Mock fetch globally
global.fetch = vi.fn();

describe('App Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Text Input → Analyze', () => {
    it('should handle text input and analyze successfully', async () => {
      const mockResponse = {
        intent: {
          analysis_type: 'sum',
          metric: 'Sales',
          group_by: ['Product'],
          time_field: null,
          top_n: null
        },
        code: 'result = df.groupby([\'Product\'])[\'Sales\'].sum()',
        target_file: 'test_data.xlsx',
        used_columns: ['Product', 'Sales'],
        result_preview: [
          { Product: 'A', Sales: 220 },
          { Product: 'B', Sales: 380 }
        ],
        columns: ['Product', 'Sales'],
        stdout: '',
        error: null
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      render(<App />);

      // Find textarea and enter question
      const textarea = screen.getByPlaceholderText(/enter your question/i);
      fireEvent.change(textarea, { target: { value: 'What is the total sales by product?' } });

      // Click analyze button
      const analyzeButton = screen.getByRole('button', { name: /analyze/i });
      fireEvent.click(analyzeButton);

      // Wait for results
      await waitFor(() => {
        expect(screen.getByText(/parsed intent/i)).toBeInTheDocument();
      });

      // Verify intent JSON is displayed
      expect(screen.getByText(/"analysis_type"/i)).toBeInTheDocument();
      expect(screen.getByText(/"sum"/i)).toBeInTheDocument();

      // Verify code is displayed
      expect(screen.getByText(/generated python code/i)).toBeInTheDocument();
      expect(screen.getByText(/groupby/i)).toBeInTheDocument();

      // Verify table is displayed
      expect(screen.getByText(/analysis result/i)).toBeInTheDocument();
      expect(screen.getByText('A')).toBeInTheDocument();
      expect(screen.getByText('220')).toBeInTheDocument();

      // Verify used columns are displayed
      expect(screen.getByText(/used columns/i)).toBeInTheDocument();
      expect(screen.getByText('Product')).toBeInTheDocument();
      expect(screen.getByText('Sales')).toBeInTheDocument();
    });

    it('should show loading state during analysis', async () => {
      (global.fetch as any).mockImplementationOnce(
        () => new Promise(resolve => setTimeout(() => resolve({
          ok: true,
          json: async () => ({})
        }), 100))
      );

      render(<App />);

      const textarea = screen.getByPlaceholderText(/enter your question/i);
      fireEvent.change(textarea, { target: { value: 'Test question' } });

      const analyzeButton = screen.getByRole('button', { name: /analyze/i });
      fireEvent.click(analyzeButton);

      // Should show loading state
      expect(screen.getByText(/analyzing/i)).toBeInTheDocument();
    });
  });

  describe('Excel File Upload', () => {
    it('should handle Excel file selection correctly', async () => {
      const mockUploadResponse = {
        file_name: 'test_data.xlsx',
        columns: ['Product', 'Sales', 'Date'],
        n_rows: 100
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUploadResponse
      });

      render(<App />);

      // Find file input
      const fileInput = screen.getByLabelText(/choose excel file/i) as HTMLInputElement;
      
      // Create a mock file
      const file = new File(['test'], 'test_data.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      
      // Simulate file selection
      Object.defineProperty(fileInput, 'files', {
        value: [file],
        writable: false
      });

      fireEvent.change(fileInput);

      // Verify file is selected
      expect(screen.getByText('test_data.xlsx')).toBeInTheDocument();

      // Click upload button
      const uploadButton = screen.getByRole('button', { name: /upload/i });
      fireEvent.click(uploadButton);

      // Wait for success message
      await waitFor(() => {
        expect(screen.getByText(/file uploaded successfully/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/rows: 100/i)).toBeInTheDocument();
      expect(screen.getByText(/columns: 3/i)).toBeInTheDocument();
    });

    it('should reject invalid file types', () => {
      render(<App />);

      const fileInput = screen.getByLabelText(/choose excel file/i) as HTMLInputElement;
      const file = new File(['test'], 'test.txt', { type: 'text/plain' });

      Object.defineProperty(fileInput, 'files', {
        value: [file],
        writable: false
      });

      fireEvent.change(fileInput);

      // Should show error
      expect(screen.getByText(/please select a valid excel file/i)).toBeInTheDocument();
    });
  });

  describe('Intent JSON Display', () => {
    it('should display Gemini intent JSON correctly', async () => {
      const mockResponse = {
        intent: {
          analysis_type: 'trend',
          metric: 'Sales',
          group_by: [],
          time_field: 'Date',
          top_n: null
        },
        code: 'result = df.resample(\'M\')[\'Sales\'].mean()',
        target_file: 'test_data.xlsx',
        used_columns: ['Sales', 'Date'],
        result_preview: [],
        columns: ['Date', 'Sales'],
        stdout: '',
        error: null
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      render(<App />);

      const textarea = screen.getByPlaceholderText(/enter your question/i);
      fireEvent.change(textarea, { target: { value: 'Show sales trend' } });

      const analyzeButton = screen.getByRole('button', { name: /analyze/i });
      fireEvent.click(analyzeButton);

      await waitFor(() => {
        const intentSection = screen.getByText(/parsed intent/i).closest('.card');
        expect(intentSection).toBeInTheDocument();
      });

      // Verify intent JSON structure
      expect(screen.getByText(/"analysis_type"/i)).toBeInTheDocument();
      expect(screen.getByText(/"trend"/i)).toBeInTheDocument();
      expect(screen.getByText(/"time_field"/i)).toBeInTheDocument();
      expect(screen.getByText(/"Date"/i)).toBeInTheDocument();
    });
  });

  describe('Python Code Generation', () => {
    it('should display auto-generated Python code', async () => {
      const mockCode = `import pandas as pd
from excel_preprocessor import preprocess_excel

df = preprocess_excel('data/test.xlsx')
result = df.groupby(['Product'])['Sales'].sum().reset_index()`;

      const mockResponse = {
        intent: { analysis_type: 'sum', metric: 'Sales', group_by: ['Product'] },
        code: mockCode,
        target_file: 'test.xlsx',
        used_columns: ['Product', 'Sales'],
        result_preview: [],
        columns: [],
        stdout: '',
        error: null
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      render(<App />);

      const textarea = screen.getByPlaceholderText(/enter your question/i);
      fireEvent.change(textarea, { target: { value: 'Sum sales by product' } });

      const analyzeButton = screen.getByRole('button', { name: /analyze/i });
      fireEvent.click(analyzeButton);

      await waitFor(() => {
        expect(screen.getByText(/generated python code/i)).toBeInTheDocument();
      });

      // Verify code is visible
      expect(screen.getByText(/import pandas/i)).toBeInTheDocument();
      expect(screen.getByText(/groupby/i)).toBeInTheDocument();
      expect(screen.getByText(/preprocess_excel/i)).toBeInTheDocument();
    });
  });

  describe('Code Execution and Results', () => {
    it('should display results table when code executes successfully', async () => {
      const mockResponse = {
        intent: { analysis_type: 'sum', metric: 'Sales', group_by: ['Product'] },
        code: 'result = df.groupby([\'Product\'])[\'Sales\'].sum()',
        target_file: 'test.xlsx',
        used_columns: ['Product', 'Sales'],
        result_preview: [
          { Product: 'A', Sales: 100 },
          { Product: 'B', Sales: 200 },
          { Product: 'C', Sales: 150 }
        ],
        columns: ['Product', 'Sales'],
        stdout: '',
        error: null
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      render(<App />);

      const textarea = screen.getByPlaceholderText(/enter your question/i);
      fireEvent.change(textarea, { target: { value: 'Sum sales' } });

      const analyzeButton = screen.getByRole('button', { name: /analyze/i });
      fireEvent.click(analyzeButton);

      await waitFor(() => {
        expect(screen.getByText(/analysis result/i)).toBeInTheDocument();
      });

      // Verify table headers
      expect(screen.getByText('Product')).toBeInTheDocument();
      expect(screen.getByText('Sales')).toBeInTheDocument();

      // Verify table data
      expect(screen.getByText('A')).toBeInTheDocument();
      expect(screen.getByText('100')).toBeInTheDocument();
      expect(screen.getByText('B')).toBeInTheDocument();
      expect(screen.getByText('200')).toBeInTheDocument();
    });

    it('should display stdout output when present', async () => {
      const mockResponse = {
        intent: { analysis_type: 'sum' },
        code: 'print("Processing data..."); result = df.sum()',
        target_file: 'test.xlsx',
        used_columns: [],
        result_preview: [],
        columns: [],
        stdout: 'Processing data...\n',
        error: null
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      render(<App />);

      const textarea = screen.getByPlaceholderText(/enter your question/i);
      fireEvent.change(textarea, { target: { value: 'Test' } });

      const analyzeButton = screen.getByRole('button', { name: /analyze/i });
      fireEvent.click(analyzeButton);

      await waitFor(() => {
        expect(screen.getByText(/output:/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/processing data/i)).toBeInTheDocument();
    });
  });

  describe('Used Columns Display', () => {
    it('should display used columns correctly', async () => {
      const mockResponse = {
        intent: { analysis_type: 'sum', metric: 'Sales', group_by: ['Product', 'Region'] },
        code: 'result = df.groupby([\'Product\', \'Region\'])[\'Sales\'].sum()',
        target_file: 'test.xlsx',
        used_columns: ['Product', 'Region', 'Sales'],
        result_preview: [],
        columns: [],
        stdout: '',
        error: null
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      render(<App />);

      const textarea = screen.getByPlaceholderText(/enter your question/i);
      fireEvent.change(textarea, { target: { value: 'Sum sales by product and region' } });

      const analyzeButton = screen.getByRole('button', { name: /analyze/i });
      fireEvent.click(analyzeButton);

      await waitFor(() => {
        expect(screen.getByText(/used columns/i)).toBeInTheDocument();
      });

      // Verify all used columns are displayed
      expect(screen.getByText('Product')).toBeInTheDocument();
      expect(screen.getByText('Region')).toBeInTheDocument();
      expect(screen.getByText('Sales')).toBeInTheDocument();
    });

    it('should handle empty used columns gracefully', async () => {
      const mockResponse = {
        intent: { analysis_type: 'groupby' },
        code: 'result = df',
        target_file: 'test.xlsx',
        used_columns: [],
        result_preview: [],
        columns: [],
        stdout: '',
        error: null
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      render(<App />);

      const textarea = screen.getByPlaceholderText(/enter your question/i);
      fireEvent.change(textarea, { target: { value: 'Show all data' } });

      const analyzeButton = screen.getByRole('button', { name: /analyze/i });
      fireEvent.click(analyzeButton);

      await waitFor(() => {
        expect(screen.getByText(/used columns/i)).toBeInTheDocument();
      });

      expect(screen.getByText(/no columns used/i)).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('should handle bad questions gracefully', async () => {
      const mockResponse = {
        intent: {},
        code: '# Error: Invalid question format',
        target_file: null,
        used_columns: [],
        result_preview: null,
        columns: null,
        stdout: '',
        error: 'Invalid question format'
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      render(<App />);

      const textarea = screen.getByPlaceholderText(/enter your question/i);
      fireEvent.change(textarea, { target: { value: 'This is a bad question' } });

      const analyzeButton = screen.getByRole('button', { name: /analyze/i });
      fireEvent.click(analyzeButton);

      await waitFor(() => {
        expect(screen.getByText(/analysis result/i)).toBeInTheDocument();
      });

      // Should display error message
      expect(screen.getByText(/invalid question format/i)).toBeInTheDocument();
    });

    it('should handle network errors gracefully', async () => {
      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      render(<App />);

      const textarea = screen.getByPlaceholderText(/enter your question/i);
      fireEvent.change(textarea, { target: { value: 'Test question' } });

      const analyzeButton = screen.getByRole('button', { name: /analyze/i });
      fireEvent.click(analyzeButton);

      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
      });
    });

    it('should handle HTTP errors gracefully', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error'
      });

      render(<App />);

      const textarea = screen.getByPlaceholderText(/enter your question/i);
      fireEvent.change(textarea, { target: { value: 'Test question' } });

      const analyzeButton = screen.getByRole('button', { name: /analyze/i });
      fireEvent.click(analyzeButton);

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument();
      });
    });

    it('should validate empty question input', () => {
      render(<App />);

      const analyzeButton = screen.getByRole('button', { name: /analyze/i });
      fireEvent.click(analyzeButton);

      // Should show error for empty question
      expect(screen.getByText(/please enter a question/i)).toBeInTheDocument();
    });
  });

  describe('Multiple Excel Files', () => {
    it('should correctly match and display target file for multiple files', async () => {
      const mockResponse = {
        intent: {
          analysis_type: 'sum',
          metric: 'Sales',
          group_by: ['Product']
        },
        code: 'result = df.groupby([\'Product\'])[\'Sales\'].sum()',
        target_file: 'sales_data.xlsx',
        used_columns: ['Product', 'Sales'],
        result_preview: [],
        columns: [],
        stdout: '',
        error: null
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      render(<App />);

      const textarea = screen.getByPlaceholderText(/enter your question/i);
      fireEvent.change(textarea, { target: { value: 'What are the sales by product?' } });

      const analyzeButton = screen.getByRole('button', { name: /analyze/i });
      fireEvent.click(analyzeButton);

      await waitFor(() => {
        // The target_file should be used in the code generation
        expect(screen.getByText(/sales_data.xlsx/i)).toBeInTheDocument();
      });
    });
  });
});

