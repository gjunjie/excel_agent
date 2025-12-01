import pandas as pd


def generate_analysis_code(file_path: str, intent: dict) -> str:
    """
    Generate a Python code string that:
      - imports pandas as pd
      - loads the preprocessed DataFrame from file_path using preprocess_excel
      - applies logic based on intent["analysis_type"]:
          - "sum"/"avg": groupby + agg on metric
          - "trend": groupby time_field (resample by month if date) and maybe group_by other cols
          - "topn": sort by metric descending and take top_n
      - assigns the final result to a variable named 'result'

    The returned string should be self-contained except for assuming that:
      - preprocess_excel is available from excel_preprocessor

    Args:
        file_path: Path to the Excel file
        intent: Dictionary with analysis_type, metric, group_by, time_field, top_n
        
    Returns:
        A string containing executable Python code
    """
    code_lines = [
        "import pandas as pd",
        "from excel_preprocessor import preprocess_excel",
        "",
        f"# Load the preprocessed DataFrame",
        f"df = preprocess_excel('{file_path}')",
        ""
    ]
    
    analysis_type = intent.get("analysis_type", "groupby")
    metric = intent.get("metric")
    group_by = intent.get("group_by", [])
    time_field = intent.get("time_field")
    top_n = intent.get("top_n")
    
    if analysis_type in ["sum", "avg"]:
        # Sum or average aggregation
        if not metric:
            code_lines.append("# Error: metric is required for sum/avg analysis")
            code_lines.append("result = None")
        else:
            agg_func = "sum" if analysis_type == "sum" else "mean"
            
            if group_by:
                # Group by specified columns and aggregate
                group_cols_str = ", ".join([f"'{col}'" for col in group_by])
                code_lines.append(f"# Group by {group_cols_str} and calculate {agg_func} of {metric}")
                code_lines.append(f"result = df.groupby([{group_cols_str}])['{metric}'].{agg_func}().reset_index()")
            else:
                # No grouping, just aggregate the entire column
                code_lines.append(f"# Calculate {agg_func} of {metric}")
                code_lines.append(f"result = pd.DataFrame({{'{metric}_{agg_func}': [df['{metric}'].{agg_func}()]}})")
    
    elif analysis_type == "trend":
        # Trend analysis with time field
        if not time_field:
            code_lines.append("# Error: time_field is required for trend analysis")
            code_lines.append("result = None")
        else:
            code_lines.append(f"# Convert {time_field} to datetime if not already")
            code_lines.append(f"df['{time_field}'] = pd.to_datetime(df['{time_field}'], errors='coerce')")
            code_lines.append("")
            
            # Check if we need to resample by month
            code_lines.append(f"# Set {time_field} as index for resampling")
            code_lines.append(f"df_trend = df.set_index('{time_field}')")
            code_lines.append("")
            
            # Determine grouping columns (excluding time_field)
            other_group_cols = [col for col in group_by if col != time_field]
            
            if metric:
                if other_group_cols:
                    # Group by other columns and resample by month
                    group_cols_str = ", ".join([f"'{col}'" for col in other_group_cols])
                    code_lines.append(f"# Group by {group_cols_str} and resample by month")
                    code_lines.append(f"result = df_trend.groupby([{group_cols_str}]).resample('M')['{metric}'].mean().reset_index()")
                else:
                    # Just resample by month
                    code_lines.append(f"# Resample by month and calculate mean of {metric}")
                    code_lines.append(f"result = df_trend.resample('M')['{metric}'].mean().reset_index()")
            else:
                # No metric specified, just resample by month (count)
                if other_group_cols:
                    group_cols_str = ", ".join([f"'{col}'" for col in other_group_cols])
                    code_lines.append(f"# Group by {group_cols_str} and resample by month (count)")
                    code_lines.append(f"result = df_trend.groupby([{group_cols_str}]).resample('M').size().reset_index(name='count')")
                else:
                    code_lines.append("# Resample by month (count)")
                    code_lines.append("result = df_trend.resample('M').size().reset_index(name='count')")
    
    elif analysis_type == "topn":
        # Top N analysis
        if not metric:
            code_lines.append("# Error: metric is required for topn analysis")
            code_lines.append("result = None")
        else:
            n = top_n if top_n else 10
            code_lines.append(f"# Sort by {metric} descending and take top {n}")
            code_lines.append(f"result = df.nlargest({n}, '{metric}')")
    
    elif analysis_type == "groupby":
        # Simple groupby
        if group_by:
            group_cols_str = ", ".join([f"'{col}'" for col in group_by])
            if metric:
                code_lines.append(f"# Group by {group_cols_str} and aggregate {metric}")
                code_lines.append(f"result = df.groupby([{group_cols_str}])['{metric}'].agg(['count', 'mean', 'sum']).reset_index()")
            else:
                code_lines.append(f"# Group by {group_cols_str} and count")
                code_lines.append(f"result = df.groupby([{group_cols_str}]).size().reset_index(name='count')")
        else:
            code_lines.append("# No group_by columns specified")
            code_lines.append("result = df")
    
    elif analysis_type == "sort":
        # Sort analysis
        if metric:
            code_lines.append(f"# Sort by {metric} descending")
            code_lines.append(f"result = df.sort_values('{metric}', ascending=False)")
        else:
            code_lines.append("# No metric specified for sorting")
            code_lines.append("result = df")
    
    else:
        # Unknown analysis type
        code_lines.append(f"# Unknown analysis_type: {analysis_type}")
        code_lines.append("result = df")
    
    return "\n".join(code_lines)

