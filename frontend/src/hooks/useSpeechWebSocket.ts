import { useRef, useCallback, useState } from 'react';

export interface WebSocketMessage {
  type: 'partial_transcript' | 'final_transcript' | 'analysis_result' | 'error' | 'status';
  text?: string;
  result?: any;
  message?: string;
}

export interface UseSpeechWebSocketReturn {
  isConnected: boolean;
  isRecording: boolean;
  partialTranscript: string;
  finalTranscript: string;
  error: string | null;
  status: string | null;
  analysisResult: any | null;
  connect: () => Promise<void>;
  disconnect: () => void;
  sendAudioChunk: (audioData: ArrayBuffer) => void;
  endRecording: () => void;
  reset: () => void;
}

export function useSpeechWebSocket(
  onAnalysisResult?: (result: any) => void
): UseSpeechWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [partialTranscript, setPartialTranscript] = useState('');
  const [finalTranscript, setFinalTranscript] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<any | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const isRecordingRef = useRef(false);

  const connect = useCallback(async () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const ws = new WebSocket('ws://localhost:8000/ws/speech');
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setError(null);
        setIsRecording(true);
        isRecordingRef.current = true;
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          
          switch (message.type) {
            case 'partial_transcript':
              if (message.text) {
                setPartialTranscript(message.text);
              }
              break;
            
            case 'final_transcript':
              if (message.text) {
                setFinalTranscript(message.text);
                setPartialTranscript('');
              }
              break;
            
            case 'analysis_result':
              if (message.result) {
                setAnalysisResult(message.result);
                if (onAnalysisResult) {
                  onAnalysisResult(message.result);
                }
              }
              break;
            
            case 'error':
              setError(message.message || 'An error occurred');
              setIsRecording(false);
              isRecordingRef.current = false;
              break;
            
            case 'status':
              setStatus(message.message || null);
              break;
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
          setError('Failed to parse server message');
        }
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('WebSocket connection error');
        setIsConnected(false);
        setIsRecording(false);
        isRecordingRef.current = false;
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        setIsRecording(false);
        
        // Attempt to reconnect after 3 seconds if we were recording
        if (isRecordingRef.current) {
          reconnectTimeoutRef.current = window.setTimeout(() => {
            connect();
          }, 3000);
        }
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('Failed to create WebSocket:', err);
      setError('Failed to connect to server');
      setIsConnected(false);
      setIsRecording(false);
      isRecordingRef.current = false;
    }
  }, [onAnalysisResult]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    isRecordingRef.current = false;
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setIsConnected(false);
    setIsRecording(false);
  }, []);

  const sendAudioChunk = useCallback((audioData: ArrayBuffer) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(audioData);
    }
  }, []);

  const endRecording = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'end' }));
    }
    setIsRecording(false);
    isRecordingRef.current = false;
  }, []);

  const reset = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'reset' }));
    }
    setPartialTranscript('');
    setFinalTranscript('');
    setError(null);
    setStatus(null);
    setAnalysisResult(null);
  }, []);

  return {
    isConnected,
    isRecording,
    partialTranscript,
    finalTranscript,
    error,
    status,
    analysisResult,
    connect,
    disconnect,
    sendAudioChunk,
    endRecording,
    reset,
  };
}

