import { useState, useRef, useEffect } from 'react';
import { useSpeechWebSocket } from '../hooks/useSpeechWebSocket';

interface SpeechRecorderProps {
  onAnalysisResult?: (result: any) => void;
}

export default function SpeechRecorder({ onAnalysisResult }: SpeechRecorderProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [recordingTime, setRecordingTime] = useState(0);
  
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const intervalRef = useRef<number | null>(null);
  const startTimeRef = useRef<number | null>(null);
  const isRecordingRef = useRef(false);

  const {
    isConnected,
    partialTranscript,
    finalTranscript,
    error,
    status,
    connect,
    disconnect,
    sendAudioChunk,
    endRecording,
    reset,
  } = useSpeechWebSocket(onAnalysisResult);

  // Request microphone permission on mount
  useEffect(() => {
    checkMicrophonePermission();
  }, []);

  const checkMicrophonePermission = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach(track => track.stop());
      setHasPermission(true);
    } catch (err) {
      console.error('Microphone permission denied:', err);
      setHasPermission(false);
    }
  };

  const startRecording = async () => {
    try {
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });

      mediaStreamRef.current = stream;

      // Create AudioContext
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({
        sampleRate: 16000,
      });
      audioContextRef.current = audioContext;

      // Create media stream source
      const source = audioContext.createMediaStreamSource(stream);

      // Create script processor for audio processing
      // Note: ScriptProcessorNode is deprecated but widely supported
      // For production, consider using AudioWorkletNode
      const bufferSize = 4096;
      const processor = audioContext.createScriptProcessor(bufferSize, 1, 1);
      processorRef.current = processor;

      processor.onaudioprocess = (event) => {
        if (!isRecordingRef.current) return;

        const inputData = event.inputBuffer.getChannelData(0);
        
        // Convert Float32Array to Int16Array (PCM format)
        const int16Data = new Int16Array(inputData.length);
        for (let i = 0; i < inputData.length; i++) {
          // Clamp and convert to 16-bit integer
          const s = Math.max(-1, Math.min(1, inputData[i]));
          int16Data[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }

        // Send audio chunk via WebSocket
        sendAudioChunk(int16Data.buffer);
      };

      source.connect(processor);
      processor.connect(audioContext.destination);

      // Connect WebSocket
      await connect();

      // Start recording timer
      setIsRecording(true);
      isRecordingRef.current = true;
      startTimeRef.current = Date.now();
      intervalRef.current = window.setInterval(() => {
        if (startTimeRef.current) {
          setRecordingTime(Math.floor((Date.now() - startTimeRef.current) / 1000));
        }
      }, 1000);

      // Reset previous transcripts
      reset();
    } catch (err) {
      console.error('Error starting recording:', err);
      setHasPermission(false);
      alert('Failed to access microphone. Please grant permission and try again.');
    }
  };

  const stopRecording = () => {
    // Stop media stream
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
      mediaStreamRef.current = null;
    }

    // Clean up audio context
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    // Stop timer
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    // End recording on server
    endRecording();

    setIsRecording(false);
    isRecordingRef.current = false;
    setRecordingTime(0);
    startTimeRef.current = null;
  };

  const handleToggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopRecording();
      disconnect();
    };
  }, [disconnect]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (hasPermission === false) {
    return (
      <div className="speech-recorder">
        <div className="error-message">
          Microphone access denied. Please grant permission to use speech recording.
        </div>
        <button
          className="retry-permission-button"
          onClick={checkMicrophonePermission}
        >
          Retry Permission
        </button>
      </div>
    );
  }

  return (
    <div className="speech-recorder">
      <div className="speech-controls">
        <button
          className={`record-button ${isRecording ? 'recording' : ''}`}
          onClick={handleToggleRecording}
          disabled={hasPermission === null}
        >
          {isRecording ? (
            <>
              <span className="record-icon stop">⏹</span>
              <span>Stop Recording</span>
              {recordingTime > 0 && (
                <span className="recording-time">{formatTime(recordingTime)}</span>
              )}
            </>
          ) : (
            <>
              <span className="record-icon">🎤</span>
              <span>Start Recording</span>
            </>
          )}
        </button>
      </div>

      {status && (
        <div className="status-message">
          {status}
        </div>
      )}

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {partialTranscript && (
        <div className="transcript partial">
          <div className="transcript-label">Listening...</div>
          <div className="transcript-text">{partialTranscript}</div>
        </div>
      )}

      {finalTranscript && (
        <div className="transcript final">
          <div className="transcript-label">Final Transcript:</div>
          <div className="transcript-text">{finalTranscript}</div>
        </div>
      )}

      {isRecording && (
        <div className="recording-indicator">
          <span className="pulse-dot"></span>
          <span>Recording in progress...</span>
        </div>
      )}
    </div>
  );
}

