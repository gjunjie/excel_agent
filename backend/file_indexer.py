import os
import json
import glob
from excel_preprocessor import preprocess_excel


def build_excel_index(data_dir: str) -> dict:
    """
    Scan all .xlsx files under data_dir, preprocess each one,
    and collect column names.
    
    Args:
        data_dir: Directory path to scan for Excel files
        
    Returns:
        Dictionary mapping file_name -> list of column names
    """
    index = {}
    
    # Find all .xlsx files in the data directory
    pattern = os.path.join(data_dir, "*.xlsx")
    excel_files = glob.glob(pattern)
    
    for file_path in excel_files:
        try:
            # Get just the filename
            file_name = os.path.basename(file_path)
            
            # Use preprocess_excel to load a cleaned DataFrame
            df = preprocess_excel(file_path)
            
            # Collect column names
            column_names = df.columns.tolist()
            
            # Map file_name -> list of column names
            index[file_name] = column_names
        except Exception as e:
            # Log error but continue processing other files
            print(f"Error processing {file_path}: {e}")
            continue
    
    return index


def save_index(index: dict, index_path: str):
    """
    Save the index as JSON.
    
    Args:
        index: Dictionary to save
        index_path: Path where to save the JSON file
    """
    # Ensure the directory exists
    os.makedirs(os.path.dirname(index_path) if os.path.dirname(index_path) else ".", exist_ok=True)
    
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)


def load_index(index_path: str) -> dict:
    """
    Load the index from JSON.
    
    Args:
        index_path: Path to the JSON file
        
    Returns:
        Dictionary mapping file_name -> list of column names
        Returns empty dict if file doesn't exist
    """
    if not os.path.exists(index_path):
        return {}
    
    try:
        with open(index_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading index from {index_path}: {e}")
        return {}


def _normalize_string(s: str) -> str:
    """
    Normalize a string for fuzzy matching: lowercase and remove spaces.
    
    Args:
        s: String to normalize
        
    Returns:
        Normalized string
    """
    if not s:
        return ""
    return s.lower().replace(" ", "").replace("_", "").replace("-", "")


def _fuzzy_match(target: str, candidates: list[str]) -> str | None:
    """
    Find the best matching candidate for a target string using fuzzy matching.
    
    Args:
        target: The string to match
        candidates: List of candidate strings to match against
        
    Returns:
        The best matching candidate, or None if no match found
    """
    if not target:
        return None
    
    normalized_target = _normalize_string(target)
    
    # First try exact match (case-insensitive)
    for candidate in candidates:
        if _normalize_string(candidate) == normalized_target:
            return candidate
    
    # Then try substring match
    for candidate in candidates:
        normalized_candidate = _normalize_string(candidate)
        if normalized_target in normalized_candidate or normalized_candidate in normalized_target:
            return candidate
    
    return None


def match_excel_file(intent: dict, index: dict) -> dict:
    """
    Given the parsed intent and the index {file_name: [columns...]},
    compute a simple overlap score:
      - +1 for each intent field (metric, group_by, time_field) that matches a column
      - Use case-insensitive and simple fuzzy matching (e.g., lowercased, remove spaces)
    
    Args:
        intent: Parsed intent dictionary with fields like metric, group_by, time_field
        index: Dictionary mapping file_name -> list of column names
        
    Returns:
        Dictionary with:
          - "file_name": best matching file name
          - "score": score between 0.0 and 1.0
          - "matched_columns": list of columns that matched intent fields
          - "used_columns": list of all columns used from the intent
    """
    best_match = None
    best_score = 0.0
    best_matched_columns = []
    best_used_columns = []
    
    # Collect all intent fields that need to be matched
    intent_fields = []
    if intent.get("metric"):
        intent_fields.append(("metric", intent["metric"]))
    if intent.get("group_by"):
        for col in intent["group_by"]:
            intent_fields.append(("group_by", col))
    if intent.get("time_field"):
        intent_fields.append(("time_field", intent["time_field"]))
    
    # If no intent fields to match, return empty result
    if not intent_fields:
        return {
            "file_name": None,
            "score": 0.0,
            "matched_columns": [],
            "used_columns": []
        }
    
    # Score each file in the index
    for file_name, columns in index.items():
        matched_columns = []
        used_columns = []
        matches = 0
        
        # First, check if metric exists (required for most analysis types)
        metric_required = intent.get("metric") is not None
        metric_matched = False
        if metric_required:
            metric_value = intent["metric"]
            matched_metric = _fuzzy_match(metric_value, columns)
            if matched_metric:
                metric_matched = True
                matches += 1
                matched_columns.append(matched_metric)
                used_columns.append(metric_value)
            else:
                # Skip this file if metric is required but not found
                continue
        
        # Check other intent fields against the file's columns
        for field_type, field_value in intent_fields:
            # Skip metric if we already processed it
            if field_type == "metric" and metric_required:
                continue
                
            matched_col = _fuzzy_match(field_value, columns)
            if matched_col:
                matches += 1
                matched_columns.append(matched_col)
                used_columns.append(field_value)
        
        # Calculate score (0.0 to 1.0)
        score = matches / len(intent_fields) if intent_fields else 0.0
        
        # Update best match if this score is better
        if score > best_score:
            best_score = score
            best_match = file_name
            best_matched_columns = matched_columns
            best_used_columns = used_columns
    
    return {
        "file_name": best_match,
        "score": best_score,
        "matched_columns": best_matched_columns,
        "used_columns": best_used_columns
    }

