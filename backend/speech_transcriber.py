"""
Speech transcription module using Faster Whisper for real-time audio transcription.
Includes a placeholder fallback if Faster Whisper is not available.
"""
import numpy as np
from typing import Optional

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    WhisperModel = None

try:
    import onnxruntime
    ONNXRUNTIME_AVAILABLE = True
except ImportError:
    ONNXRUNTIME_AVAILABLE = False


class SpeechTranscriber:
    """Handles speech transcription using Faster Whisper or a placeholder."""
    
    def __init__(self, model_size: str = "base", device: str = "cpu", compute_type: str = "int8"):
        """
        Initialize the transcriber.
        
        Args:
            model_size: Whisper model size ("tiny", "base", "small", "medium", "large-v2", "large-v3")
                       Ignored if Faster Whisper is not available.
            device: Device to use ("cpu", "cuda", "auto")
            compute_type: Compute type ("int8", "int8_float16", "int16", "float16", "float32")
        """
        self.model = None
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.audio_buffer = []
        
        if FASTER_WHISPER_AVAILABLE:
            try:
                print(f"Loading Faster Whisper model: {model_size} (device: {device}, compute_type: {compute_type})")
                self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
                print("Faster Whisper model loaded successfully")
            except Exception as e:
                print(f"Warning: Failed to load Faster Whisper model: {e}")
                print("Falling back to placeholder transcription")
                self.model = None
        else:
            print("Faster Whisper not available. Using placeholder transcription.")
    
    def transcribe_audio_chunk(self, audio_bytes: bytes, sample_rate: int = 16000) -> Optional[str]:
        """
        Transcribe a single audio chunk.
        
        Args:
            audio_bytes: Raw audio bytes (PCM format)
            sample_rate: Sample rate in Hz (default: 16000)
            
        Returns:
            Transcribed text or None if transcription fails
        """
        if not self.model:
            # Placeholder: return None for now, will accumulate and transcribe on final
            return None
        
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Transcribe using Faster Whisper
            # Disable VAD if onnxruntime is not available
            vad_enabled = ONNXRUNTIME_AVAILABLE
            segments, info = self.model.transcribe(
                audio_array,
                language="en",
                beam_size=5,
                vad_filter=vad_enabled
            )
            
            # Collect all segments into text
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text)
            
            return " ".join(text_parts).strip()
        except Exception as e:
            print(f"Error transcribing audio chunk: {e}")
            return None
    
    def transcribe_final(self, audio_bytes: bytes, sample_rate: int = 16000) -> str:
        """
        Transcribe the final accumulated audio.
        
        Args:
            audio_bytes: Complete audio bytes (PCM format)
            sample_rate: Sample rate in Hz (default: 16000)
            
        Returns:
            Final transcribed text
        """
        if not self.model:
            # Placeholder: return a mock transcription
            duration = len(audio_bytes) / (sample_rate * 2)  # 2 bytes per sample (int16)
            return f"[Placeholder transcription for {duration:.1f}s of audio. Install faster-whisper for real transcription.]"
        
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Transcribe using Faster Whisper
            # Disable VAD if onnxruntime is not available
            vad_enabled = ONNXRUNTIME_AVAILABLE
            segments, info = self.model.transcribe(
                audio_array,
                language="en",
                beam_size=5,
                vad_filter=vad_enabled
            )
            
            # Collect all segments into text
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text)
            
            transcribed_text = " ".join(text_parts).strip()
            return transcribed_text if transcribed_text else "[No speech detected]"
        except Exception as e:
            print(f"Error transcribing final audio: {e}")
            return f"[Transcription error: {str(e)}]"


# Global transcriber instance (lazy-loaded)
_transcriber: Optional[SpeechTranscriber] = None


def get_transcriber() -> SpeechTranscriber:
    """Get or create the global transcriber instance."""
    global _transcriber
    if _transcriber is None:
        _transcriber = SpeechTranscriber()
    return _transcriber

