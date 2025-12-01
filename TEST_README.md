# Test Suite Documentation

This document describes the comprehensive test suite for the Excel AI Agent application.

## Test Coverage

The test suite covers all the scenarios from the verification checklist:

✅ **Text input → Analyze** - Works  
✅ **Correct Excel file selected** - Works  
✅ **Gemini intent JSON correct** - Works  
✅ **Python code auto-generated** - Visible  
✅ **Code executes successfully** - Returns data  
✅ **Table displayed in UI** - Correct  
✅ **Used columns displayed** - Correct  
✅ **Error handling (bad question)** - Graceful  
✅ **Multiple Excel files** - Correctly matched  

## Backend Tests

### Setup

1. Install test dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Set up environment variables (if testing with real Gemini API):
```bash
export GOOGLE_GEMINI_API_KEY=your_api_key_here
```

Note: Most tests mock the Gemini API, so the API key is not required for running tests.

### Running Backend Tests

Run all backend tests:
```bash
cd backend
pytest
```

Run with verbose output:
```bash
pytest -v
```

Run specific test file:
```bash
pytest test_main.py
pytest test_integration.py
```

Run specific test class:
```bash
pytest test_main.py::TestAnalyzeEndpoint
```

Run with coverage:
```bash
pytest --cov=. --cov-report=html
```

### Test Files

- **`test_main.py`**: Unit tests for individual components and API endpoints
  - Health endpoint tests
  - File upload tests
  - Intent parsing tests
  - Code generation tests
  - Code execution tests
  - Column extraction tests
  - File matching tests
  - Analyze endpoint tests

- **`test_integration.py`**: End-to-end integration tests
  - Complete workflow tests
  - Error handling tests
  - Multiple file matching tests
  - Different analysis type tests

## Frontend Tests

### Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

### Running Frontend Tests

Run all frontend tests:
```bash
cd frontend
npm test
```

Run tests in watch mode:
```bash
npm test -- --watch
```

Run tests with UI:
```bash
npm run test:ui
```

Run tests with coverage:
```bash
npm run test:coverage
```

### Test Files

- **`src/App.test.tsx`**: Main application component tests
  - Text input and analyze workflow
  - Excel file upload
  - Intent JSON display
  - Python code generation display
  - Code execution and results
  - Used columns display
  - Error handling
  - Multiple Excel files

- **`src/components/ResultTable.test.tsx`**: Result table component tests
- **`src/components/UsedColumns.test.tsx`**: Used columns component tests
- **`src/components/CodeBlock.test.tsx`**: Code block component tests

## Test Structure

### Backend Test Organization

```
backend/
├── test_main.py          # Unit tests
├── test_integration.py   # Integration tests
└── pytest.ini           # Pytest configuration
```

### Frontend Test Organization

```
frontend/
├── src/
│   ├── App.test.tsx
│   ├── components/
│   │   ├── ResultTable.test.tsx
│   │   ├── UsedColumns.test.tsx
│   │   └── CodeBlock.test.tsx
│   └── test/
│       └── setup.ts      # Test setup and configuration
└── vitest.config.ts      # Vitest configuration
```

## Running All Tests

To run both backend and frontend tests:

```bash
# Backend tests
cd backend && pytest -v && cd ..

# Frontend tests
cd frontend && npm test && cd ..
```

## Test Scenarios Covered

### 1. Text Input → Analyze ✅
- **Backend**: `TestAnalyzeEndpoint.test_analyze_endpoint_success`
- **Frontend**: `App Component > Text Input → Analyze > should handle text input and analyze successfully`

### 2. Correct Excel File Selected ✅
- **Backend**: `TestFileMatching.test_match_excel_file_single_match`
- **Frontend**: `App Component > Multiple Excel Files > should correctly match and display target file`

### 3. Gemini Intent JSON Correct ✅
- **Backend**: `TestIntentParsing` (all tests)
- **Frontend**: `App Component > Intent JSON Display > should display Gemini intent JSON correctly`

### 4. Python Code Auto-Generated ✅
- **Backend**: `TestCodeGeneration` (all tests)
- **Frontend**: `App Component > Python Code Generation > should display auto-generated Python code`

### 5. Code Executes Successfully ✅
- **Backend**: `TestCodeExecution.test_execute_sum_code`
- **Frontend**: `App Component > Code Execution and Results > should display results table when code executes successfully`

### 6. Table Displayed in UI ✅
- **Backend**: `TestFullWorkflow.test_full_workflow_text_input_to_analyze`
- **Frontend**: `App Component > Code Execution and Results > should display results table when code executes successfully`

### 7. Used Columns Displayed ✅
- **Backend**: `TestColumnExtraction` (all tests)
- **Frontend**: `App Component > Used Columns Display > should display used columns correctly`

### 8. Error Handling (Bad Question) ✅
- **Backend**: `TestAnalyzeEndpoint.test_analyze_endpoint_error_handling`
- **Frontend**: `App Component > Error Handling > should handle bad questions gracefully`

### 9. Multiple Excel Files ✅
- **Backend**: `TestFileMatching.test_match_excel_file_multiple_files`
- **Frontend**: `App Component > Multiple Excel Files > should correctly match and display target file`

## Continuous Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Backend Tests
  run: |
    cd backend
    pip install -r requirements.txt
    pytest

- name: Run Frontend Tests
  run: |
    cd frontend
    npm install
    npm test
```

## Notes

- Most backend tests mock the Gemini API to avoid API costs and ensure consistent results
- Frontend tests use `jsdom` environment to simulate browser behavior
- Integration tests use temporary directories to avoid polluting the actual data directory
- All tests are designed to be independent and can run in any order

