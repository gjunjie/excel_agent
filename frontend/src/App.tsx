import { useState, useRef } from 'react';
import CodeBlock from './components/CodeBlock';
import ResultTable from './components/ResultTable';
import UsedColumns from './components/UsedColumns';
import SpeechRecorder from './components/SpeechRecorder';

interface AnalyzeResponse {
  intent: any;
  code: string;
  target_file: string;
  used_columns: string[];
  result_preview: any[] | null;
  columns: string[] | null;
  stdout: string;
  error: string | null;
}

interface UploadResponse {
  file_name: string;
  columns: string[];
  n_rows: number;
}

function App() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<AnalyzeResponse | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<UploadResponse | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // Validate file type
      const validExtensions = ['.xlsx', '.xls'];
      const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
      if (!validExtensions.includes(fileExtension)) {
        setUploadError('Please select a valid Excel file (.xlsx or .xls)');
        setSelectedFile(null);
        return;
      }
      setSelectedFile(file);
      setUploadError(null);
      setUploadSuccess(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setUploadError('Please select a file first');
      return;
    }

    setUploading(true);
    setUploadError(null);
    setUploadSuccess(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch('http://localhost:8000/upload_excel', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        let errorMessage = `HTTP error! status: ${response.status}`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorData.error || errorMessage;
        } catch {
          errorMessage = response.statusText || errorMessage;
        }
        throw new Error(errorMessage);
      }

      const result: UploadResponse = await response.json();
      setUploadSuccess(result);
      setSelectedFile(null);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Failed to upload file');
    } finally {
      setUploading(false);
    }
  };

  const handleAnalyze = async () => {
    if (!question.trim()) {
      setError('Please enter a question');
      return;
    }

    setLoading(true);
    setError(null);
    setData(null);

    try {
      const response = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question }),
      });

      if (!response.ok) {
        // Try to get error message from response
        let errorMessage = `HTTP error! status: ${response.status}`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorData.error || errorMessage;
        } catch {
          // If response is not JSON, use status text
          errorMessage = response.statusText || errorMessage;
        }
        throw new Error(errorMessage);
      }

      const result: AnalyzeResponse = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze');
    } finally {
      setLoading(false);
    }
  };

  const handleSpeechAnalysisResult = (result: AnalyzeResponse) => {
    setData(result);
    setError(null);
    // Optionally set the question from the final transcript
    // This will be handled by the SpeechRecorder component if needed
  };

  return (
    <div className="app">
      <div className="top-section">
        <h1>Excel AI Agent</h1>
        
        {/* File Upload Section */}
        <div className="upload-section">
          <h2>Upload Excel File</h2>
          <div className="upload-group">
            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx,.xls"
              onChange={handleFileSelect}
              className="file-input"
              id="file-upload"
              disabled={uploading}
            />
            <label htmlFor="file-upload" className="file-label">
              {selectedFile ? (
                <>
                  <span>✓</span>
                  <span style={{ fontWeight: 600, color: 'var(--success)' }}>
                    {selectedFile.name}
                  </span>
                </>
              ) : (
                'Choose Excel file...'
              )}
            </label>
            <button
              className="upload-button"
              onClick={handleUpload}
              disabled={uploading || !selectedFile}
            >
              {uploading ? (
                <>
                  <span className="loading-spinner"></span>
                  Uploading...
                </>
              ) : (
                'Upload'
              )}
            </button>
          </div>
          {uploadError && <div className="error-message">{uploadError}</div>}
          {uploadSuccess && (
            <div className="success-message">
              <strong>File uploaded successfully!</strong>
              <div className="upload-info">
                <div>File: {uploadSuccess.file_name}</div>
                <div>Rows: {uploadSuccess.n_rows.toLocaleString()}</div>
                <div>Columns: {uploadSuccess.columns.length}</div>
              </div>
            </div>
          )}
        </div>

        {/* Analysis Section */}
        <div className="analysis-section">
          <h2>Analyze Data</h2>
          
          {/* Speech Recording Section */}
          <div className="speech-section">
            <h3>🎤 Voice Input</h3>
            <SpeechRecorder onAnalysisResult={handleSpeechAnalysisResult} />
          </div>

          <div className="divider">
            <span>or</span>
          </div>

          {/* Text Input Section */}
          <div className="text-input-section">
            <h3>✍️ Text Input</h3>
            <div className="input-group">
              <textarea
                className="question-input"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Enter your question about the Excel data..."
                rows={3}
                disabled={loading}
              />
              <button
                className="analyze-button"
                onClick={handleAnalyze}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <span className="loading-spinner"></span>
                    Analyzing...
                  </>
                ) : (
                  'Analyze'
                )}
              </button>
            </div>
            {error && <div className="error-message">{error}</div>}
          </div>
        </div>
      </div>

      {data && (
        <div className="main-section">
          <div className="left-column">
            <div className="card">
              <h2>
                <span>💡</span>
                Parsed Intent
              </h2>
              <pre className="json-display">
                {JSON.stringify(data.intent, null, 2)}
              </pre>
            </div>
            <div className="card">
              <h2>
                <span>🐍</span>
                Generated Python Code
              </h2>
              <CodeBlock code={data.code} />
            </div>
          </div>
          <div className="right-column">
            <div className="card">
              <h2>
                <span>📈</span>
                Analysis Result
              </h2>
              {data.error ? (
                <div className="error-message">{data.error}</div>
              ) : (
                <ResultTable
                  result={data.result_preview}
                  columns={data.columns}
                />
              )}
              {data.stdout && (
                <div className="stdout">
                  <strong>Output:</strong>
                  <pre>{data.stdout}</pre>
                </div>
              )}
            </div>
            <div className="card">
              <h2>
                <span>📋</span>
                Used Columns
              </h2>
              <UsedColumns columns={data.used_columns} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
