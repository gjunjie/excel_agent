import os
import json
import asyncio
from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from excel_preprocessor import preprocess_excel
from file_indexer import build_excel_index, save_index, load_index, match_excel_file
from intent_parser import parse_intent
from code_generator import generate_analysis_code
from code_runner import run_analysis_code
from column_lineage import extract_used_columns
from speech_transcriber import get_transcriber

app = FastAPI()

# Enable CORS for localhost:5173 (Vite default port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = "data"
INDEX_PATH = os.path.join(DATA_DIR, "index.json")


@app.on_event("startup")
async def startup_event():
    """Ensure data folder exists on startup."""
    os.makedirs(DATA_DIR, exist_ok=True)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/list_files")
async def list_files():
    """
    List all Excel files in the database with their metadata.
    
    Returns:
        Dictionary with:
          - "files": list of file objects, each containing:
            - "file_name": name of the file
            - "columns": list of column names
            - "n_columns": number of columns
            - "n_rows": number of rows (if available)
    """
    try:
        # Load the index
        try:
            index = load_index(INDEX_PATH)
        except FileNotFoundError:
            # Build index if it doesn't exist
            index = build_excel_index(DATA_DIR)
            save_index(index, INDEX_PATH)
        
        # Get file metadata
        files = []
        for file_name, columns in index.items():
            file_info = {
                "file_name": file_name,
                "columns": columns,
                "n_columns": len(columns)
            }
            
            # Try to get row count by loading the file
            try:
                file_path = os.path.join(DATA_DIR, file_name)
                if os.path.exists(file_path):
                    df = preprocess_excel(file_path)
                    file_info["n_rows"] = len(df)
                else:
                    file_info["n_rows"] = None
            except Exception as e:
                # If we can't load the file, just skip row count
                file_info["n_rows"] = None
            
            files.append(file_info)
        
        return {"files": files}
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in /list_files endpoint: {e}\n{error_trace}")
        return {"files": [], "error": str(e)}


@app.post("/upload_excel")
async def upload_excel(file: UploadFile = File(...)):
    """
    Upload an Excel file, save it to the data folder, preprocess it,
    and return file information.
    """
    # Save the uploaded file
    file_path = os.path.join(DATA_DIR, file.filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Preprocess the Excel file
    df = preprocess_excel(file_path)
    
    # Rebuild the index and save it
    index = build_excel_index(DATA_DIR)
    save_index(index, INDEX_PATH)
    
    # Return file information
    return {
        "file_name": file.filename,
        "columns": df.columns.tolist(),
        "n_rows": len(df)
    }


class AnalyzePlanRequest(BaseModel):
    question: str


class ExecuteCodeRequest(BaseModel):
    code: str


@app.post("/analyze/plan")
async def analyze_plan(request: AnalyzePlanRequest):
    """
    Analyze a question and determine which Excel file best matches the intent.
    
    Args:
        request: Request body containing the question
        
    Returns:
        Dictionary with:
          - "intent": parsed intent dictionary
          - "target_file": best matching file name
          - "score": match score (0.0 to 1.0)
    """
    # Load the index
    index = load_index(INDEX_PATH)
    
    # Aggregate all columns from all files as available_columns
    available_columns = []
    for columns in index.values():
        available_columns.extend(columns)
    # Remove duplicates while preserving order
    available_columns = list(dict.fromkeys(available_columns))
    
    # Parse the intent from the question
    intent = parse_intent(request.question, available_columns)
    
    # Match the intent against the index
    match_result = match_excel_file(intent, index)
    
    return {
        "intent": intent,
        "target_file": match_result["file_name"],
        "score": match_result["score"]
    }


@app.post("/analyze/code")
async def analyze_code(request: AnalyzePlanRequest):
    """
    Analyze a question, determine which Excel file best matches the intent,
    and generate Python code to perform the analysis.
    
    Args:
        request: Request body containing the question
        
    Returns:
        Dictionary with:
          - "code": generated Python code string
          - "intent": parsed intent dictionary
          - "target_file": best matching file name
          - "used_columns": list of column names used in the code
    """
    # Load the index
    index = load_index(INDEX_PATH)
    
    # Aggregate all columns from all files as available_columns
    available_columns = []
    for columns in index.values():
        available_columns.extend(columns)
    # Remove duplicates while preserving order
    available_columns = list(dict.fromkeys(available_columns))
    
    # Parse the intent from the question
    intent = parse_intent(request.question, available_columns)
    
    # Match the intent against the index
    match_result = match_excel_file(intent, index)
    target_file = match_result["file_name"]
    
    # Generate code if we have a target file
    if target_file:
        file_path = os.path.join(DATA_DIR, target_file)
        code = generate_analysis_code(file_path, intent)
    else:
        code = "# Error: No matching file found for the given question"
    
    # Extract used columns from the generated code
    used_columns = extract_used_columns(code)
    
    return {
        "code": code,
        "intent": intent,
        "target_file": target_file,
        "used_columns": used_columns
    }


@app.post("/analyze/execute")
async def analyze_execute(request: ExecuteCodeRequest):
    """
    Execute generated analysis code and return the results.
    
    Args:
        request: Request body containing the code to execute
        
    Returns:
        Dictionary with:
          - "result_preview": preview of the result (first 50 rows as records)
          - "columns": list of column names (if result is a DataFrame)
          - "stdout": captured stdout output
          - "error": error message if execution failed, null otherwise
    """
    # Prepare extra globals that might be needed
    globals_extra = {}
    
    # Execute the code and return results
    result = run_analysis_code(request.code, globals_extra)
    
    return result


@app.post("/analyze")
async def analyze(request: AnalyzePlanRequest):
    """
    Complete analysis workflow: parse intent, generate code, execute, and return all results.
    
    Args:
        request: Request body containing the question
        
    Returns:
        Dictionary with:
          - "intent": parsed intent dictionary
          - "code": generated Python code string
          - "target_file": best matching file name
          - "used_columns": list of column names used in the code
          - "result_preview": preview of the result (first 50 rows as records)
          - "columns": list of column names (if result is a DataFrame)
          - "stdout": captured stdout output
          - "error": error message if execution failed, null otherwise
    """
    try:
        # Load the index
        try:
            index = load_index(INDEX_PATH)
        except FileNotFoundError:
            # Build index if it doesn't exist
            index = build_excel_index(DATA_DIR)
            save_index(index, INDEX_PATH)
        
        # Aggregate all columns from all files as available_columns
        available_columns = []
        for columns in index.values():
            available_columns.extend(columns)
        # Remove duplicates while preserving order
        available_columns = list(dict.fromkeys(available_columns))
        
        # Parse the intent from the question
        intent = parse_intent(request.question, available_columns)
        
        # Match the intent against the index
        match_result = match_excel_file(intent, index)
        target_file = match_result["file_name"]
        
        # Generate code if we have a target file
        if target_file:
            file_path = os.path.join(DATA_DIR, target_file)
            code = generate_analysis_code(file_path, intent)
        else:
            code = "# Error: No matching file found for the given question"
        
        # Extract used columns from the generated code
        used_columns = extract_used_columns(code)
        
        # Execute the code
        globals_extra = {}
        execution_result = run_analysis_code(code, globals_extra)
        
        # Combine all results
        return {
            "intent": intent,
            "code": code,
            "target_file": target_file,
            "used_columns": used_columns,
            **execution_result
        }
    except Exception as e:
        # Return error in a structured format
        import traceback
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"Error in /analyze endpoint: {error_msg}\n{error_trace}")
        return {
            "intent": {},
            "code": f"# Error: {error_msg}",
            "target_file": None,
            "used_columns": [],
            "result_preview": None,
            "columns": None,
            "stdout": "",
            "error": error_msg
        }


async def run_analysis_pipeline(question: str) -> dict:
    """
    Run the complete analysis pipeline (same as /analyze endpoint).
    
    Args:
        question: The question to analyze
        
    Returns:
        Dictionary with analysis results
    """
    try:
        # Load the index
        try:
            index = load_index(INDEX_PATH)
        except FileNotFoundError:
            # Build index if it doesn't exist
            index = build_excel_index(DATA_DIR)
            save_index(index, INDEX_PATH)
        
        # Aggregate all columns from all files as available_columns
        available_columns = []
        for columns in index.values():
            available_columns.extend(columns)
        # Remove duplicates while preserving order
        available_columns = list(dict.fromkeys(available_columns))
        
        # Parse the intent from the question
        intent = parse_intent(question, available_columns)
        
        # Match the intent against the index
        match_result = match_excel_file(intent, index)
        target_file = match_result["file_name"]
        
        # Generate code if we have a target file
        if target_file:
            file_path = os.path.join(DATA_DIR, target_file)
            code = generate_analysis_code(file_path, intent)
        else:
            code = "# Error: No matching file found for the given question"
        
        # Extract used columns from the generated code
        used_columns = extract_used_columns(code)
        
        # Execute the code
        globals_extra = {}
        execution_result = run_analysis_code(code, globals_extra)
        
        # Combine all results
        return {
            "intent": intent,
            "code": code,
            "target_file": target_file,
            "used_columns": used_columns,
            **execution_result
        }
    except Exception as e:
        # Return error in a structured format
        import traceback
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"Error in analysis pipeline: {error_msg}\n{error_trace}")
        return {
            "intent": {},
            "code": f"# Error: {error_msg}",
            "target_file": None,
            "used_columns": [],
            "result_preview": None,
            "columns": None,
            "stdout": "",
            "error": error_msg
        }


@app.websocket("/ws/speech")
async def websocket_speech(websocket: WebSocket):
    """
    WebSocket endpoint for speech-to-text analysis.
    
    Accepts audio chunks (16kHz PCM), transcribes them using Whisper,
    and runs the analysis pipeline when speech stops.
    
    Message format from client:
    - Binary: Audio chunk bytes (PCM, 16kHz, 16-bit)
    - Text JSON: Control messages like {"type": "end"} to signal end of speech
    
    Message format to client:
    - {"type": "partial_transcript", "text": "..."}
    - {"type": "final_transcript", "text": "..."}
    - {"type": "analysis_result", "result": {...}}
    - {"type": "error", "message": "..."}
    - {"type": "status", "message": "..."}
    """
    await websocket.accept()
    
    transcriber = get_transcriber()
    audio_buffer = bytearray()
    last_chunk_time = [asyncio.get_event_loop().time()]  # Use list for mutable reference
    silence_timeout = 2.0  # 2 seconds of silence to trigger final transcription
    partial_transcript_interval = 1.0  # Send partial transcripts every 1 second
    last_partial_time = [asyncio.get_event_loop().time()]  # Use list for mutable reference
    sample_rate = 16000  # 16kHz
    
    # Task for handling silence timeout
    timeout_task = None
    processing = False  # Flag to prevent concurrent processing
    
    async def send_message(message_type: str, data: dict):
        """Helper to send JSON messages to client."""
        try:
            await websocket.send_json({
                "type": message_type,
                **data
            })
        except Exception as e:
            print(f"Error sending message: {e}")
    
    async def process_final_transcript():
        """Process the accumulated audio and run analysis."""
        nonlocal audio_buffer, processing, timeout_task
        
        if processing or len(audio_buffer) == 0:
            return
        
        processing = True
        
        try:
            # Cancel timeout task
            if timeout_task and not timeout_task.done():
                timeout_task.cancel()
                timeout_task = None
            
            # Process final transcription
            final_text = transcriber.transcribe_final(bytes(audio_buffer), sample_rate)
            await send_message("final_transcript", {"text": final_text})
            
            # Run analysis pipeline
            if final_text and not final_text.startswith("[Placeholder") and not final_text.startswith("[Transcription error"):
                await send_message("status", {"message": "Analyzing..."})
                analysis_result = await run_analysis_pipeline(final_text)
                await send_message("analysis_result", {"result": analysis_result})
            else:
                await send_message("error", {"message": "Could not transcribe audio. Please try again."})
            
            # Reset buffer
            audio_buffer = bytearray()
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error processing final transcript: {e}\n{error_trace}")
            await send_message("error", {"message": f"Error processing audio: {str(e)}"})
            audio_buffer = bytearray()
        finally:
            processing = False
    
    async def check_silence_timeout():
        """Check if we've had silence for too long and process final transcript."""
        nonlocal timeout_task
        try:
            while True:
                await asyncio.sleep(0.2)  # Check every 200ms
                
                if processing:
                    continue
                
                current_time = asyncio.get_event_loop().time()
                time_since_last_chunk = current_time - last_chunk_time[0]
                
                if time_since_last_chunk >= silence_timeout and len(audio_buffer) > 0:
                    await process_final_transcript()
                    break
        except asyncio.CancelledError:
            pass
    
    async def check_partial_transcript():
        """Periodically send partial transcripts during active speech."""
        nonlocal last_partial_time
        try:
            while True:
                await asyncio.sleep(partial_transcript_interval)
                
                if processing or len(audio_buffer) == 0:
                    continue
                
                current_time = asyncio.get_event_loop().time()
                time_since_last_chunk = current_time - last_chunk_time[0]
                
                # Only send partial if we're actively receiving audio (within last 0.5s)
                if time_since_last_chunk < 0.5 and transcriber.model is not None:
                    try:
                        # For partial transcripts, we'll transcribe the current buffer
                        # Note: This is simplified - in production, use streaming Whisper
                        partial_text = transcriber.transcribe_final(bytes(audio_buffer), sample_rate)
                        if partial_text and not partial_text.startswith("[Placeholder"):
                            await send_message("partial_transcript", {"text": partial_text})
                    except Exception as e:
                        # Silently fail for partial transcripts
                        pass
        except asyncio.CancelledError:
            pass
    
    # Start partial transcript task
    partial_task = asyncio.create_task(check_partial_transcript())
    
    try:
        while True:
            # Wait for either binary audio data or text control messages
            try:
                data = await asyncio.wait_for(websocket.receive(), timeout=0.1)
            except asyncio.TimeoutError:
                continue
            
            if "bytes" in data:
                # Received audio chunk
                audio_chunk = data["bytes"]
                audio_buffer.extend(audio_chunk)
                last_chunk_time[0] = asyncio.get_event_loop().time()
                
                # Start or restart timeout task
                if timeout_task is None or timeout_task.done():
                    timeout_task = asyncio.create_task(check_silence_timeout())
                
            elif "text" in data:
                # Received text control message
                try:
                    message = json.loads(data["text"])
                    msg_type = message.get("type")
                    
                    if msg_type == "end":
                        # Client explicitly ended speech
                        await process_final_transcript()
                    
                    elif msg_type == "reset":
                        # Reset the buffer
                        audio_buffer = bytearray()
                        if timeout_task and not timeout_task.done():
                            timeout_task.cancel()
                        timeout_task = None
                    
                except json.JSONDecodeError:
                    await send_message("error", {"message": "Invalid JSON message"})
    
    except WebSocketDisconnect:
        print("WebSocket client disconnected")
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in WebSocket endpoint: {e}\n{error_trace}")
        try:
            await send_message("error", {"message": f"Server error: {str(e)}"})
        except:
            pass
    finally:
        # Cleanup
        if timeout_task and not timeout_task.done():
            timeout_task.cancel()
        if partial_task and not partial_task.done():
            partial_task.cancel()

