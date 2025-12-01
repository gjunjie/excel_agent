import re


def extract_used_columns(code: str) -> list[str]:
    """
    Parse the code string and extract DataFrame column names.
    Look for patterns like:
      df["col_name"]
      df['col_name']
      df.groupby(['col_name'])
      df['col_name'].method()
      df.nlargest(n, 'col_name')
    Return a unique list of column names in the order they appear.
    """
    # Pattern 1: Match df["col_name"] or df['col_name'] or variable["col_name"]
    pattern1 = r'\w+\[["\']([^"\']+)["\']\]'
    
    # Pattern 2: Match groupby(['col_name']) or groupby(["col_name"])
    pattern2 = r'groupby\(\[["\']([^"\']+)["\']\]\)'
    
    # Pattern 3: Match .nlargest(n, 'col_name') or .nsmallest(n, "col_name")
    pattern3 = r'\.n(?:largest|smallest)\([^,]+,\s*["\']([^"\']+)["\']\)'
    
    # Pattern 4: Match .sort_values('col_name') or .sort_values("col_name")
    pattern4 = r'\.sort_values\(["\']([^"\']+)["\']\)'
    
    # Pattern 5: Match resample('M')['col_name'] or similar
    pattern5 = r'\[["\']([^"\']+)["\']\]'
    
    # Find all matches
    all_matches = []
    all_matches.extend(re.findall(pattern1, code))
    all_matches.extend(re.findall(pattern2, code))
    all_matches.extend(re.findall(pattern3, code))
    all_matches.extend(re.findall(pattern4, code))
    
    # For pattern5, we need to be more careful - only match after certain contexts
    # like resample, groupby results, etc.
    resample_matches = re.findall(r'resample\([^\)]+\)\[["\']([^"\']+)["\']\]', code)
    all_matches.extend(resample_matches)
    
    # Also catch columns in groupby lists: groupby(['col1', 'col2'])
    groupby_list_matches = re.findall(r'groupby\(\[([^\]]+)\]\)', code)
    for match in groupby_list_matches:
        # Extract individual column names from the list
        col_matches = re.findall(r'["\']([^"\']+)["\']', match)
        all_matches.extend(col_matches)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_columns = []
    for col in all_matches:
        col = col.strip()
        if col and col not in seen:
            seen.add(col)
            unique_columns.append(col)
    
    return unique_columns

