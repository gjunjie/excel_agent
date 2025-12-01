import sys
import io
import traceback
from typing import Dict, Any
import pandas as pd
import numpy as np
from excel_preprocessor import preprocess_excel

# Try to import matplotlib (optional dependency)
try:
    import matplotlib
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    matplotlib = None
    plt = None


def run_analysis_code(code: str, globals_extra: dict) -> dict:
    """
    Safely execute the generated code in a restricted namespace.

    - Allowed modules: pandas, numpy, matplotlib, excel_preprocessor
    - Inject preprocess_excel into the globals
    - Capture:
        - 'result' variable (assumed to be a DataFrame or Series)
        - any printed output (stdout)
    - Return:
      {
        "result_preview": result.head(50).to_dict(orient="records"),  # limit rows
        "columns": list(result.columns) if DataFrame,
        "stdout": "...",
        "error": null or error message
      }
    """
    # Create a restricted globals namespace
    import builtins
    restricted_globals = {
        '__builtins__': {
            'print': print,
            'len': len,
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'list': list,
            'dict': dict,
            'tuple': tuple,
            'set': set,
            'range': range,
            'enumerate': enumerate,
            'zip': zip,
            'min': min,
            'max': max,
            'sum': sum,
            'abs': abs,
            'round': round,
            'sorted': sorted,
            'reversed': reversed,
            'isinstance': isinstance,
            'type': type,
            'hasattr': hasattr,
            'getattr': getattr,
            'setattr': setattr,
            '__import__': __import__,
            'True': True,
            'False': False,
            'None': None,
        },
        'pd': pd,
        'pandas': pd,
        'np': np,
        'numpy': np,
        'preprocess_excel': preprocess_excel,
    }
    
    # Add matplotlib if available
    if HAS_MATPLOTLIB:
        restricted_globals['matplotlib'] = matplotlib
        restricted_globals['plt'] = plt
        restricted_globals['pyplot'] = plt
    
    # Add any extra globals provided
    restricted_globals.update(globals_extra)
    
    # Create a local namespace
    local_namespace = {}
    
    # Capture stdout
    stdout_capture = io.StringIO()
    old_stdout = sys.stdout
    
    error = None
    result = None
    columns = None
    result_preview = None
    
    try:
        # Redirect stdout to capture print statements
        sys.stdout = stdout_capture
        
        # Execute the code
        exec(code, restricted_globals, local_namespace)
        
        # Check for 'result' variable in local namespace first, then globals
        if 'result' in local_namespace:
            result = local_namespace['result']
        elif 'result' in restricted_globals:
            result = restricted_globals['result']
        
        # Process the result if it exists
        if result is not None:
            if isinstance(result, (pd.DataFrame, pd.Series)):
                # Limit to 50 rows for preview
                if isinstance(result, pd.DataFrame):
                    preview_df = result.head(50)
                    result_preview = preview_df.to_dict(orient="records")
                    columns = list(result.columns)
                else:  # Series
                    preview_series = result.head(50)
                    result_preview = preview_series.to_dict()
                    columns = [result.name] if result.name else ['value']
            else:
                # If result is not a DataFrame/Series, try to convert it
                error = f"Result is not a DataFrame or Series, got {type(result).__name__}"
        
    except Exception as e:
        error = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
    
    finally:
        # Restore stdout
        sys.stdout = old_stdout
        stdout_content = stdout_capture.getvalue()
    
    return {
        "result_preview": result_preview,
        "columns": columns,
        "stdout": stdout_content,
        "error": error
    }

