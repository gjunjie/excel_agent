import { useState, useRef, useEffect } from 'react';
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

interface FileInfo {
  file_name: string;
  columns: string[];
  n_columns: number;
  n_rows: number | null;
}

interface FilesListResponse {
  files: FileInfo[];
  error?: string;
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
  const [filesList, setFilesList] = useState<FileInfo[]>([]);
  const [loadingFiles, setLoadingFiles] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Fetch list of files on component mount and after upload
  const fetchFilesList = async () => {
    setLoadingFiles(true);
    try {
      const response = await fetch('http://localhost:8000/list_files');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const result: FilesListResponse = await response.json();
      if (result.error) {
        console.error('Error fetching files:', result.error);
        setFilesList([]);
      } else {
        setFilesList(result.files);
      }
    } catch (err) {
      console.error('Failed to fetch files list:', err);
      setFilesList([]);
    } finally {
      setLoadingFiles(false);
    }
  };

  useEffect(() => {
    fetchFilesList();
  }, []);

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
      // Refresh files list after successful upload
      await fetchFilesList();
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
      {/* Header Section */}
      <header className="app-header">
        <h1>Excel AI Agent</h1>
        <p className="app-subtitle">Intelligent Data Analysis & Insights</p>
      </header>

      {/* Main Content Area */}
      <div className="app-content">
        {/* Left Sidebar - File Upload & Status */}
        <aside className="sidebar">
          <div className="sidebar-section">
            <h2 className="sidebar-title">
              <span>📊</span>
              File Management
            </h2>
            <div className="upload-container">
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
                    <span className="file-name">{selectedFile.name}</span>
                  </>
                ) : (
                  <>
                    <span>📁</span>
                    <span>Choose Excel file...</span>
                  </>
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
                  <>
                    <span>⬆️</span>
                    Upload
                  </>
                )}
              </button>
            </div>
            {uploadError && <div className="error-message">{uploadError}</div>}
            {uploadSuccess && (
              <div className="success-message">
                <strong>✓ File uploaded successfully!</strong>
                <div className="upload-info">
                  <div className="info-item">
                    <span className="info-label">File:</span>
                    <span className="info-value">{uploadSuccess.file_name}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Rows:</span>
                    <span className="info-value">{uploadSuccess.n_rows.toLocaleString()}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Columns:</span>
                    <span className="info-value">{uploadSuccess.columns.length}</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Files List Section */}
          <div className="sidebar-section">
            <h2 className="sidebar-title">
              <span>📁</span>
              Files in Database
            </h2>
            {loadingFiles ? (
              <div className="files-loading">
                <span className="loading-spinner"></span>
                Loading files...
              </div>
            ) : filesList.length === 0 ? (
              <div className="empty-files-state">
                No files uploaded yet. Upload an Excel file to get started.
              </div>
            ) : (
              <div className="files-list">
                {filesList.map((file, index) => (
                  <div key={index} className="file-item">
                    <div className="file-item-header">
                      <span className="file-icon">📊</span>
                      <span className="file-item-name" title={file.file_name}>
                        {file.file_name}
                      </span>
                    </div>
                    <div className="file-item-details">
                      <div className="file-detail">
                        <span className="file-detail-label">Columns:</span>
                        <span className="file-detail-value">{file.n_columns}</span>
                      </div>
                      {file.n_rows !== null && (
                        <div className="file-detail">
                          <span className="file-detail-label">Rows:</span>
                          <span className="file-detail-value">{file.n_rows.toLocaleString()}</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </aside>

        {/* Center Panel - Input Section */}
        <main className="main-panel">
          <div className="input-panel">
            <h2 className="panel-title">
              <span>🔍</span>
              Ask Your Question
            </h2>
            
            {/* Input Sections Side by Side */}
            <div className="input-sections-grid">
              {/* Speech Input */}
              <div className="input-section">
                <h3 className="input-section-title">
                  <span>🎤</span>
                  Voice Input
                </h3>
                <SpeechRecorder onAnalysisResult={handleSpeechAnalysisResult} />
              </div>
              
              {/* Text Input */}
              <div className="input-section">
                <h3 className="input-section-title">
                  <span>✍️</span>
                  Text Input
                </h3>
                <div className="text-input-wrapper">
                  <textarea
                    className="question-input"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="Enter your question about the Excel data..."
                    rows={4}
                    disabled={loading}
                  />
                  <button
                    className="analyze-button"
                    onClick={handleAnalyze}
                    disabled={loading || !question.trim()}
                  >
                    {loading ? (
                      <>
                        <span className="loading-spinner"></span>
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <span>🚀</span>
                        Analyze
                      </>
                    )}
                  </button>
                </div>
                {error && <div className="error-message">{error}</div>}
              </div>
            </div>
          </div>

          {/* Results Section */}
          {data && (
            <div className="results-panel">
              <h2 className="panel-title">
                <span>📊</span>
                Analysis Results
              </h2>
              
              <div className="results-grid">
                {/* Top Row - Intent & Columns */}
                <div className="result-card intent-card">
                  <h3 className="card-header">
                    <span>💡</span>
                    Parsed Intent
                  </h3>
                  <div className="card-content">
                    <pre className="json-display">
                      {JSON.stringify(data.intent, null, 2)}
                    </pre>
                  </div>
                </div>

                <div className="result-card columns-card">
                  <h3 className="card-header">
                    <span>📋</span>
                    Used Columns
                  </h3>
                  <div className="card-content">
                    <UsedColumns columns={data.used_columns} />
                  </div>
                </div>

                {/* Bottom Row - Code & Results */}
                <div className="result-card code-card">
                  <h3 className="card-header">
                    <span>🐍</span>
                    Generated Python Code
                  </h3>
                  <div className="card-content">
                    <CodeBlock code={data.code} />
                  </div>
                </div>

                <div className="result-card result-card-large">
                  <h3 className="card-header">
                    <span>📈</span>
                    Analysis Result
                  </h3>
                  <div className="card-content">
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
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
