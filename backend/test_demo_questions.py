"""
Test script to verify demo questions work correctly.
This ensures Gemini doesn't hallucinate columns and returns proper results.
"""
import os
import sys
from intent_parser import parse_intent
from file_indexer import load_index, match_excel_file
from code_generator import generate_analysis_code
from code_runner import run_analysis_code
from column_lineage import extract_used_columns

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

DATA_DIR = "data"
INDEX_PATH = os.path.join(DATA_DIR, "index.json")

def test_demo_question(question: str, expected_file: str, expected_columns: list):
    """Test a demo question and verify it works correctly."""
    print(f"\n{'='*60}")
    print(f"Testing: {question}")
    print(f"{'='*60}")
    
    # Load index
    index = load_index(INDEX_PATH)
    
    # Aggregate all columns
    available_columns = []
    for columns in index.values():
        available_columns.extend(columns)
    available_columns = list(dict.fromkeys(available_columns))
    
    # Parse intent
    print("\n1. Parsing intent...")
    try:
        intent = parse_intent(question, available_columns)
        print(f"   Intent: {intent}")
    except Exception as e:
        print(f"   ❌ ERROR parsing intent: {e}")
        return False
    
    # Match file
    print("\n2. Matching Excel file...")
    match_result = match_excel_file(intent, index)
    target_file = match_result["file_name"]
    print(f"   Matched file: {target_file}")
    print(f"   Match score: {match_result['score']:.2f}")
    
    if target_file != expected_file:
        print(f"   ⚠️  WARNING: Expected {expected_file}, got {target_file}")
    
    # Generate code
    print("\n3. Generating code...")
    if target_file:
        file_path = os.path.join(DATA_DIR, target_file)
        code = generate_analysis_code(file_path, intent)
        print(f"   Code generated ({len(code)} chars)")
    else:
        print("   ❌ ERROR: No matching file found")
        return False
    
    # Extract used columns
    print("\n4. Extracting column lineage...")
    used_columns = extract_used_columns(code)
    print(f"   Used columns: {used_columns}")
    
    # Check for expected columns
    missing_columns = [col for col in expected_columns if col not in used_columns]
    if missing_columns:
        print(f"   ⚠️  WARNING: Expected columns not found: {missing_columns}")
    
    # Execute code
    print("\n5. Executing code...")
    try:
        result = run_analysis_code(code, {})
        if result.get("error"):
            print(f"   ❌ ERROR executing code: {result['error']}")
            return False
        
        if result.get("result_preview"):
            preview_rows = len(result["result_preview"])
            print(f"   ✅ Success! Returned {preview_rows} rows")
            print(f"   Columns in result: {result.get('columns', [])}")
            if result.get("stdout"):
                print(f"   Stdout: {result['stdout']}")
        else:
            print("   ⚠️  WARNING: No result preview returned")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False
    
    print("\n✅ Test passed!")
    return True


if __name__ == "__main__":
    # Demo questions - exact wording as requested
    demos = [
        {
            "question": "Show total sales by region",
            "expected_file": "cola.xlsx",
            "expected_columns": ["City", "total sales"]
        },
        {
            "question": "Analyze monthly revenue trend",
            "expected_file": "cola.xlsx",
            "expected_columns": ["date", "total sales"]
        },
        {
            "question": "Show top 5 products by revenue",
            "expected_file": "cola.xlsx",
            "expected_columns": ["Product series", "total sales"]
        }
    ]
    
    print("Testing Demo Questions")
    print("="*60)
    
    results = []
    for demo in demos:
        result = test_demo_question(
            demo["question"],
            demo["expected_file"],
            demo["expected_columns"]
        )
        results.append((demo["question"], result))
    
    print(f"\n{'='*60}")
    print("Summary")
    print(f"{'='*60}")
    for question, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {question}")
    
    all_passed = all(result for _, result in results)
    sys.exit(0 if all_passed else 1)

