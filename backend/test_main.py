"""
Comprehensive test suite for the Excel AI Agent backend.

Tests cover:
1. Text input → Analyze
2. Correct Excel file selected
3. Gemini intent JSON correct
4. Python code auto-generated
5. Code executes successfully
6. Used columns displayed
7. Error handling (bad question)
8. Multiple Excel files
"""
import os
import json
import pytest
import pandas as pd
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

from main import app
from intent_parser import parse_intent
from code_generator import generate_analysis_code
from code_runner import run_analysis_code
from file_indexer import build_excel_index, match_excel_file
from column_lineage import extract_used_columns

# Create test client
client = TestClient(app)


@pytest.fixture
def temp_data_dir():
    """Create a temporary data directory for testing."""
    temp_dir = tempfile.mkdtemp()
    
    # Patch DATA_DIR in main module
    import main
    original_dir = main.DATA_DIR
    original_index_path = main.INDEX_PATH
    main.DATA_DIR = temp_dir
    main.INDEX_PATH = os.path.join(temp_dir, "index.json")
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)
    main.DATA_DIR = original_dir
    main.INDEX_PATH = original_index_path


@pytest.fixture
def sample_excel_file(temp_data_dir):
    """Create a sample Excel file for testing."""
    file_path = os.path.join(temp_data_dir, "test_data.xlsx")
    
    # Create sample data
    df = pd.DataFrame({
        'Product': ['A', 'B', 'C', 'A', 'B'],
        'Sales': [100, 200, 150, 120, 180],
        'Date': pd.date_range('2024-01-01', periods=5, freq='D'),
        'Region': ['North', 'South', 'North', 'South', 'North']
    })
    
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def multiple_excel_files(temp_data_dir):
    """Create multiple Excel files for testing file matching."""
    files = {}
    
    # File 1: Sales data
    df1 = pd.DataFrame({
        'Product': ['A', 'B', 'C'],
        'Sales': [100, 200, 150],
        'Date': pd.date_range('2024-01-01', periods=3, freq='D')
    })
    file1 = os.path.join(temp_data_dir, "sales_data.xlsx")
    df1.to_excel(file1, index=False)
    files['sales'] = file1
    
    # File 2: Budget data
    df2 = pd.DataFrame({
        'Department': ['IT', 'HR', 'Finance'],
        'Budget': [50000, 30000, 40000],
        'Year': [2024, 2024, 2024]
    })
    file2 = os.path.join(temp_data_dir, "budget_data.xlsx")
    df2.to_excel(file2, index=False)
    files['budget'] = file2
    
    return files


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_endpoint(self):
        """Test that health endpoint returns ok."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestFileUpload:
    """Test Excel file upload functionality."""
    
    def test_upload_excel_file(self, temp_data_dir, sample_excel_file):
        """Test uploading an Excel file."""
        with open(sample_excel_file, 'rb') as f:
            response = client.post(
                "/upload_excel",
                files={"file": ("test_data.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["file_name"] == "test_data.xlsx"
        assert "columns" in data
        assert "n_rows" in data
        assert len(data["columns"]) > 0
        assert data["n_rows"] > 0


class TestIntentParsing:
    """Test intent parsing with Gemini API."""
    
    @patch('intent_parser.genai')
    def test_parse_intent_sum(self, mock_genai):
        """Test parsing a sum intent."""
        # Mock Gemini response
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = '{"analysis_type": "sum", "metric": "Sales", "group_by": ["Product"], "time_field": null, "top_n": null}'
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.configure = Mock()
        
        available_columns = ["Product", "Sales", "Date"]
        intent = parse_intent("What is the total sales by product?", available_columns)
        
        assert intent["analysis_type"] == "sum"
        assert intent["metric"] == "Sales"
        assert "Product" in intent["group_by"]
    
    @patch('intent_parser.genai')
    def test_parse_intent_avg(self, mock_genai):
        """Test parsing an average intent."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = '{"analysis_type": "avg", "metric": "Sales", "group_by": [], "time_field": null, "top_n": null}'
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.configure = Mock()
        
        available_columns = ["Sales", "Product"]
        intent = parse_intent("What is the average sales?", available_columns)
        
        assert intent["analysis_type"] == "avg"
        assert intent["metric"] == "Sales"
    
    @patch('intent_parser.genai')
    def test_parse_intent_trend(self, mock_genai):
        """Test parsing a trend intent."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = '{"analysis_type": "trend", "metric": "Sales", "group_by": [], "time_field": "Date", "top_n": null}'
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.configure = Mock()
        
        available_columns = ["Sales", "Date"]
        intent = parse_intent("Show me sales trend over time", available_columns)
        
        assert intent["analysis_type"] == "trend"
        assert intent["time_field"] == "Date"
        assert intent["metric"] == "Sales"
    
    @patch('intent_parser.genai')
    def test_parse_intent_topn(self, mock_genai):
        """Test parsing a top N intent."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = '{"analysis_type": "topn", "metric": "Sales", "group_by": [], "time_field": null, "top_n": 5}'
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.configure = Mock()
        
        available_columns = ["Sales", "Product"]
        intent = parse_intent("Show me top 5 products by sales", available_columns)
        
        assert intent["analysis_type"] == "topn"
        assert intent["metric"] == "Sales"
        assert intent["top_n"] == 5
    
    @patch('intent_parser.genai')
    def test_parse_intent_with_markdown(self, mock_genai):
        """Test parsing intent when Gemini returns markdown wrapped JSON."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = '```json\n{"analysis_type": "sum", "metric": "Sales", "group_by": ["Product"], "time_field": null, "top_n": null}\n```'
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.configure = Mock()
        
        available_columns = ["Product", "Sales"]
        intent = parse_intent("Sum sales by product", available_columns)
        
        assert intent["analysis_type"] == "sum"
        assert intent["metric"] == "Sales"


class TestCodeGeneration:
    """Test Python code generation."""
    
    def test_generate_sum_code(self, sample_excel_file):
        """Test generating code for sum analysis."""
        intent = {
            "analysis_type": "sum",
            "metric": "Sales",
            "group_by": ["Product"],
            "time_field": None,
            "top_n": None
        }
        
        code = generate_analysis_code(sample_excel_file, intent)
        
        assert "import pandas as pd" in code
        assert "preprocess_excel" in code
        assert "groupby" in code
        assert "Sales" in code
        assert "Product" in code
        assert "result" in code
    
    def test_generate_avg_code(self, sample_excel_file):
        """Test generating code for average analysis."""
        intent = {
            "analysis_type": "avg",
            "metric": "Sales",
            "group_by": [],
            "time_field": None,
            "top_n": None
        }
        
        code = generate_analysis_code(sample_excel_file, intent)
        
        assert "mean()" in code or "avg" in code.lower()
        assert "Sales" in code
    
    def test_generate_trend_code(self, sample_excel_file):
        """Test generating code for trend analysis."""
        intent = {
            "analysis_type": "trend",
            "metric": "Sales",
            "group_by": [],
            "time_field": "Date",
            "top_n": None
        }
        
        code = generate_analysis_code(sample_excel_file, intent)
        
        assert "to_datetime" in code
        assert "resample" in code
        assert "Date" in code
        assert "Sales" in code
    
    def test_generate_topn_code(self, sample_excel_file):
        """Test generating code for top N analysis."""
        intent = {
            "analysis_type": "topn",
            "metric": "Sales",
            "group_by": [],
            "time_field": None,
            "top_n": 5
        }
        
        code = generate_analysis_code(sample_excel_file, intent)
        
        assert "nlargest" in code or "sort_values" in code
        assert "5" in code
        assert "Sales" in code


class TestCodeExecution:
    """Test code execution."""
    
    def test_execute_sum_code(self, sample_excel_file):
        """Test executing generated sum code."""
        intent = {
            "analysis_type": "sum",
            "metric": "Sales",
            "group_by": ["Product"],
            "time_field": None,
            "top_n": None
        }
        
        code = generate_analysis_code(sample_excel_file, intent)
        result = run_analysis_code(code, {})
        
        assert result["error"] is None
        assert result["result_preview"] is not None
        assert result["columns"] is not None
        assert len(result["result_preview"]) > 0
    
    def test_execute_avg_code(self, sample_excel_file):
        """Test executing generated average code."""
        intent = {
            "analysis_type": "avg",
            "metric": "Sales",
            "group_by": [],
            "time_field": None,
            "top_n": None
        }
        
        code = generate_analysis_code(sample_excel_file, intent)
        result = run_analysis_code(code, {})
        
        assert result["error"] is None
        assert result["result_preview"] is not None
    
    def test_execute_code_with_error(self):
        """Test executing invalid code returns error gracefully."""
        invalid_code = "result = undefined_variable + 1"
        result = run_analysis_code(invalid_code, {})
        
        assert result["error"] is not None
        assert "NameError" in result["error"] or "error" in result["error"].lower()


class TestColumnExtraction:
    """Test used columns extraction."""
    
    def test_extract_used_columns(self):
        """Test extracting used columns from code."""
        code = '''
        df = preprocess_excel('file.xlsx')
        result = df.groupby(['Product'])['Sales'].sum().reset_index()
        '''
        
        columns = extract_used_columns(code)
        
        assert "Product" in columns
        assert "Sales" in columns
    
    def test_extract_used_columns_multiple(self):
        """Test extracting multiple columns."""
        code = '''
        df = preprocess_excel('file.xlsx')
        df['Date'] = pd.to_datetime(df['Date'])
        result = df.groupby(['Product', 'Region'])['Sales'].mean()
        '''
        
        columns = extract_used_columns(code)
        
        assert "Date" in columns
        assert "Product" in columns
        assert "Region" in columns
        assert "Sales" in columns
    
    def test_extract_used_columns_no_duplicates(self):
        """Test that duplicate columns are removed."""
        code = '''
        df = preprocess_excel('file.xlsx')
        result = df[['Sales', 'Product', 'Sales']]
        '''
        
        columns = extract_used_columns(code)
        
        # Should only have one instance of Sales
        assert columns.count("Sales") == 1


class TestFileMatching:
    """Test Excel file matching logic."""
    
    def test_match_excel_file_single_match(self, temp_data_dir, multiple_excel_files):
        """Test matching a single file correctly."""
        index = build_excel_index(temp_data_dir)
        
        intent = {
            "analysis_type": "sum",
            "metric": "Sales",
            "group_by": ["Product"],
            "time_field": None,
            "top_n": None
        }
        
        match_result = match_excel_file(intent, index)
        
        assert match_result["file_name"] == "sales_data.xlsx"
        assert match_result["score"] > 0.0
    
    def test_match_excel_file_multiple_files(self, temp_data_dir, multiple_excel_files):
        """Test matching correct file when multiple files exist."""
        index = build_excel_index(temp_data_dir)
        
        # Intent for budget data
        intent = {
            "analysis_type": "sum",
            "metric": "Budget",
            "group_by": ["Department"],
            "time_field": None,
            "top_n": None
        }
        
        match_result = match_excel_file(intent, index)
        
        assert match_result["file_name"] == "budget_data.xlsx"
        assert match_result["score"] > 0.0
    
    def test_match_excel_file_no_match(self, temp_data_dir, multiple_excel_files):
        """Test handling when no file matches."""
        index = build_excel_index(temp_data_dir)
        
        intent = {
            "analysis_type": "sum",
            "metric": "NonExistentColumn",
            "group_by": [],
            "time_field": None,
            "top_n": None
        }
        
        match_result = match_excel_file(intent, index)
        
        # Should return None or a file with low score
        assert match_result["file_name"] is None or match_result["score"] == 0.0


class TestAnalyzeEndpoint:
    """Test the main /analyze endpoint."""
    
    @patch('main.parse_intent')
    @patch('main.match_excel_file')
    @patch('main.generate_analysis_code')
    @patch('main.run_analysis_code')
    @patch('main.load_index')
    def test_analyze_endpoint_success(
        self, mock_load_index, mock_run_code, mock_gen_code, 
        mock_match_file, mock_parse_intent, temp_data_dir, sample_excel_file
    ):
        """Test successful analysis workflow."""
        # Setup mocks
        mock_load_index.return_value = {"test_data.xlsx": ["Product", "Sales", "Date"]}
        mock_parse_intent.return_value = {
            "analysis_type": "sum",
            "metric": "Sales",
            "group_by": ["Product"],
            "time_field": None,
            "top_n": None
        }
        mock_match_file.return_value = {
            "file_name": "test_data.xlsx",
            "score": 1.0
        }
        mock_gen_code.return_value = "result = df.groupby(['Product'])['Sales'].sum()"
        mock_run_code.return_value = {
            "result_preview": [{"Product": "A", "Sales": 220}],
            "columns": ["Product", "Sales"],
            "stdout": "",
            "error": None
        }
        
        response = client.post(
            "/analyze",
            json={"question": "What is the total sales by product?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "intent" in data
        assert "code" in data
        assert "target_file" in data
        assert "used_columns" in data
        assert "result_preview" in data
        assert data["error"] is None
    
    @patch('main.parse_intent')
    @patch('main.load_index')
    def test_analyze_endpoint_error_handling(
        self, mock_load_index, mock_parse_intent, temp_data_dir
    ):
        """Test error handling for bad questions."""
        # Setup mocks to raise an error
        mock_load_index.return_value = {}
        mock_parse_intent.side_effect = Exception("Invalid question format")
        
        response = client.post(
            "/analyze",
            json={"question": "This is a bad question that will cause an error"}
        )
        
        assert response.status_code == 200  # Endpoint should return 200 even on error
        data = response.json()
        assert "error" in data
        assert data["error"] is not None
        assert data["code"] is not None
        assert "# Error" in data["code"] or "Error" in data["code"]


class TestFullWorkflow:
    """Test complete end-to-end workflows."""
    
    @patch('intent_parser.genai')
    def test_full_workflow_text_input_to_analyze(
        self, mock_genai, temp_data_dir, sample_excel_file
    ):
        """Test complete workflow: text input → analyze → results."""
        # Mock Gemini
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = '{"analysis_type": "sum", "metric": "Sales", "group_by": ["Product"], "time_field": null, "top_n": null}'
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.configure = Mock()
        
        # Build index
        index = build_excel_index(temp_data_dir)
        import main
        from file_indexer import save_index
        save_index(index, main.INDEX_PATH)
        
        # Make request
        response = client.post(
            "/analyze",
            json={"question": "What is the total sales by product?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify intent JSON is correct
        assert data["intent"]["analysis_type"] == "sum"
        assert data["intent"]["metric"] == "Sales"
        
        # Verify correct file was selected
        assert data["target_file"] == "test_data.xlsx"
        
        # Verify code was generated
        assert data["code"] is not None
        assert len(data["code"]) > 0
        
        # Verify code executes successfully
        assert data["error"] is None
        assert data["result_preview"] is not None
        
        # Verify used columns are displayed
        assert "used_columns" in data
        assert len(data["used_columns"]) > 0
    
    @patch('intent_parser.genai')
    def test_multiple_excel_files_correctly_matched(
        self, mock_genai, temp_data_dir, multiple_excel_files
    ):
        """Test that multiple Excel files are correctly matched."""
        # Mock Gemini for sales question
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = '{"analysis_type": "sum", "metric": "Sales", "group_by": ["Product"], "time_field": null, "top_n": null}'
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.configure = Mock()
        
        # Build index
        index = build_excel_index(temp_data_dir)
        import main
        from file_indexer import save_index
        save_index(index, main.INDEX_PATH)
        
        # Test sales question
        response = client.post(
            "/analyze",
            json={"question": "What are the total sales by product?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["target_file"] == "sales_data.xlsx"
        
        # Test budget question
        mock_response.text = '{"analysis_type": "sum", "metric": "Budget", "group_by": ["Department"], "time_field": null, "top_n": null}'
        response = client.post(
            "/analyze",
            json={"question": "What is the total budget by department?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["target_file"] == "budget_data.xlsx"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

