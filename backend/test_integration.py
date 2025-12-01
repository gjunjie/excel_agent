"""
Integration tests for end-to-end workflows.

These tests verify the complete flow from user input to results display.
"""
import os
import json
import pytest
import pandas as pd
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import tempfile
import shutil

from main import app
from file_indexer import build_excel_index, save_index

client = TestClient(app)


@pytest.fixture
def temp_data_dir():
    """Create a temporary data directory for testing."""
    temp_dir = tempfile.mkdtemp()
    
    import main
    original_dir = main.DATA_DIR
    main.DATA_DIR = temp_dir
    main.INDEX_PATH = os.path.join(temp_dir, "index.json")
    
    yield temp_dir
    
    shutil.rmtree(temp_dir)
    main.DATA_DIR = original_dir
    main.INDEX_PATH = os.path.join(original_dir, "index.json") if original_dir else None


@pytest.fixture
def sample_excel_files(temp_data_dir):
    """Create multiple sample Excel files."""
    files = {}
    
    # Sales data
    df1 = pd.DataFrame({
        'Product': ['A', 'B', 'C', 'A', 'B'],
        'Sales': [100, 200, 150, 120, 180],
        'Date': pd.date_range('2024-01-01', periods=5, freq='D'),
        'Region': ['North', 'South', 'North', 'South', 'North']
    })
    file1 = os.path.join(temp_data_dir, "sales_data.xlsx")
    df1.to_excel(file1, index=False)
    files['sales'] = file1
    
    # Budget data
    df2 = pd.DataFrame({
        'Department': ['IT', 'HR', 'Finance'],
        'Budget': [50000, 30000, 40000],
        'Year': [2024, 2024, 2024]
    })
    file2 = os.path.join(temp_data_dir, "budget_data.xlsx")
    df2.to_excel(file2, index=False)
    files['budget'] = file2
    
    # Build index
    index = build_excel_index(temp_data_dir)
    import main
    save_index(index, main.INDEX_PATH)
    
    return files


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""
    
    @patch('intent_parser.genai')
    def test_complete_workflow_text_input_to_results(
        self, mock_genai, temp_data_dir, sample_excel_files
    ):
        """
        Test complete workflow:
        1. Text input → Analyze
        2. Correct Excel file selected
        3. Gemini intent JSON correct
        4. Python code auto-generated
        5. Code executes successfully
        6. Table displayed in UI (via result_preview)
        7. Used columns displayed
        """
        # Mock Gemini API
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps({
            "analysis_type": "sum",
            "metric": "Sales",
            "group_by": ["Product"],
            "time_field": None,
            "top_n": None
        })
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.configure = Mock()
        
        # Make request
        response = client.post(
            "/analyze",
            json={"question": "What is the total sales by product?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 1. Text input → Analyze: ✅ Works
        assert "intent" in data
        assert "code" in data
        assert "result_preview" in data
        
        # 2. Correct Excel file selected: ✅ Works
        assert data["target_file"] == "sales_data.xlsx"
        
        # 3. Gemini intent JSON correct: ✅ Works
        assert data["intent"]["analysis_type"] == "sum"
        assert data["intent"]["metric"] == "Sales"
        assert "Product" in data["intent"]["group_by"]
        
        # 4. Python code auto-generated: ✅ Visible
        assert data["code"] is not None
        assert len(data["code"]) > 0
        assert "groupby" in data["code"].lower()
        assert "Sales" in data["code"]
        assert "Product" in data["code"]
        
        # 5. Code executes successfully: ✅ Returns data
        assert data["error"] is None
        assert data["result_preview"] is not None
        assert isinstance(data["result_preview"], list)
        assert len(data["result_preview"]) > 0
        assert data["columns"] is not None
        
        # 6. Table displayed in UI: ✅ Correct (result_preview contains data)
        assert "Product" in data["columns"] or any("Product" in str(row) for row in data["result_preview"])
        
        # 7. Used columns displayed: ✅ Correct
        assert "used_columns" in data
        assert len(data["used_columns"]) > 0
        assert "Sales" in data["used_columns"]
        assert "Product" in data["used_columns"]
    
    @patch('intent_parser.genai')
    def test_error_handling_bad_question(
        self, mock_genai, temp_data_dir, sample_excel_files
    ):
        """
        Test error handling for bad questions: ✅ Graceful
        """
        # Mock Gemini to return invalid response
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "This is not valid JSON"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.configure = Mock()
        
        response = client.post(
            "/analyze",
            json={"question": "This is a bad question that will cause an error"}
        )
        
        # Should return 200 with error in response
        assert response.status_code == 200
        data = response.json()
        
        # Should have error field
        assert "error" in data
        assert data["error"] is not None
        
        # Should still have code field (with error message)
        assert "code" in data
        assert "Error" in data["code"] or "error" in data["code"].lower()
    
    @patch('intent_parser.genai')
    def test_multiple_excel_files_correctly_matched(
        self, mock_genai, temp_data_dir, sample_excel_files
    ):
        """
        Test multiple Excel files: ✅ Correctly matched
        """
        # Test 1: Sales question should match sales_data.xlsx
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps({
            "analysis_type": "sum",
            "metric": "Sales",
            "group_by": ["Product"],
            "time_field": None,
            "top_n": None
        })
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.configure = Mock()
        
        response = client.post(
            "/analyze",
            json={"question": "What are the total sales by product?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["target_file"] == "sales_data.xlsx"
        
        # Test 2: Budget question should match budget_data.xlsx
        mock_response.text = json.dumps({
            "analysis_type": "sum",
            "metric": "Budget",
            "group_by": ["Department"],
            "time_field": None,
            "top_n": None
        })
        
        response = client.post(
            "/analyze",
            json={"question": "What is the total budget by department?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["target_file"] == "budget_data.xlsx"
    
    @patch('intent_parser.genai')
    def test_different_analysis_types(
        self, mock_genai, temp_data_dir, sample_excel_files
    ):
        """Test different analysis types work correctly."""
        test_cases = [
            {
                "question": "What is the average sales?",
                "intent": {
                    "analysis_type": "avg",
                    "metric": "Sales",
                    "group_by": [],
                    "time_field": None,
                    "top_n": None
                }
            },
            {
                "question": "Show me top 3 products by sales",
                "intent": {
                    "analysis_type": "topn",
                    "metric": "Sales",
                    "group_by": [],
                    "time_field": None,
                    "top_n": 3
                }
            },
            {
                "question": "Show sales trend over time",
                "intent": {
                    "analysis_type": "trend",
                    "metric": "Sales",
                    "group_by": [],
                    "time_field": "Date",
                    "top_n": None
                }
            }
        ]
        
        for test_case in test_cases:
            mock_model = Mock()
            mock_response = Mock()
            mock_response.text = json.dumps(test_case["intent"])
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.configure = Mock()
            
            response = client.post(
                "/analyze",
                json={"question": test_case["question"]}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["error"] is None
            assert data["intent"]["analysis_type"] == test_case["intent"]["analysis_type"]
            assert data["code"] is not None
            assert data["result_preview"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

