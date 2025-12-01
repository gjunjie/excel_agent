import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def _build_prompt(question: str, available_columns: list[str]) -> str:
    """
    Build a prompt for the LLM to parse the user's intent.
    
    Args:
        question: The natural language question from the user
        available_columns: List of available column names in the dataset
        
    Returns:
        A formatted prompt string
    """
    columns_str = ", ".join([f'"{col}"' for col in available_columns])
    
    prompt = f"""You are a data analysis assistant. Parse the following natural language question into a structured intent.

Available columns in the dataset: [{columns_str}]

User question: "{question}"

Analyze the question and return a JSON object with the following structure:
- "analysis_type": one of ["sum", "avg", "trend", "groupby", "sort", "topn"] (required)
- "metric": the numeric column name to aggregate on (if applicable, otherwise null)
- "group_by": list of column names to group by (if applicable, otherwise empty list)
- "time_field": time-related column name if the question involves time/date analysis (otherwise null)
- "top_n": integer if user asks for top N items (otherwise null)

Guidelines:
1. Map semantic names in the question to the closest matching column names from the available columns list
2. For "sum" and "avg", identify the numeric column to aggregate
3. For "groupby", identify which columns to group by
4. For "trend", identify the time field and metric
5. For "sort", identify the column to sort by
6. For "topn", identify the number N and the column to rank by
7. Use exact column names from the available_columns list
8. If a column cannot be matched, use null or empty list as appropriate

Respond ONLY with valid JSON, no additional text or explanation."""

    return prompt


def parse_intent(question: str, available_columns: list[str]) -> dict:
    """
    Use an LLM to parse the natural language question into a structured intent.
    
    Args:
        question: The natural language question from the user
        available_columns: List of available column names in the dataset
        
    Returns:
        A dict with fields:
          - "analysis_type": one of ["sum", "avg", "trend", "groupby", "sort", "topn"]
          - "metric": the numeric column name to aggregate on (if any)
          - "group_by": list of column names to group by (if any)
          - "time_field": time-related column name (if any)
          - "top_n": integer if user asks for top N
    """
    # Get API key from environment variable
    api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_GEMINI_API_KEY environment variable is not set. "
            "Please set it in your .env file or environment."
        )
    
    # Configure the Gemini API
    genai.configure(api_key=api_key)
    
    # Build the prompt
    prompt = _build_prompt(question, available_columns)
    
    # Initialize the model
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    response_text = None
    try:
        # Generate response
        response = model.generate_content(prompt)
        
        # Extract text from response
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]  # Remove ```json
        elif response_text.startswith("```"):
            response_text = response_text[3:]  # Remove ```
        
        if response_text.endswith("```"):
            response_text = response_text[:-3]  # Remove closing ```
        
        response_text = response_text.strip()
        
        # Parse JSON response
        intent = json.loads(response_text)
        
        # Validate and set defaults for required fields
        valid_analysis_types = ["sum", "avg", "trend", "groupby", "sort", "topn"]
        if intent.get("analysis_type") not in valid_analysis_types:
            # Default to "groupby" if invalid
            intent["analysis_type"] = "groupby"
        
        # Ensure all fields are present with proper defaults
        result = {
            "analysis_type": intent.get("analysis_type", "groupby"),
            "metric": intent.get("metric"),
            "group_by": intent.get("group_by", []),
            "time_field": intent.get("time_field"),
            "top_n": intent.get("top_n")
        }
        
        return result
        
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse LLM response as JSON: {e}"
        if response_text:
            error_msg += f". Response was: {response_text}"
        raise ValueError(error_msg)
    except Exception as e:
        raise RuntimeError(f"Error calling Gemini API: {e}")

