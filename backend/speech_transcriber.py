"""
Speech transcription module using Whisper for real-time audio transcription.
Includes a placeholder fallback if Whisper is not available.
"""
import numpy as np
from typing import Optional

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    whisper = None


class SpeechTranscriber:
    """Handles speech transcription using Whisper or a placeholder."""
    
    def __init__(self, model_size: str = "base"):
        """
        Initialize the transcriber.
        
        Args:
            model_size: Whisper model size ("tiny", "base", "small", "medium", "large")
                       Ignored if Whisper is not available.
        """
        self.model = None
        self.model_size = model_size
        self.audio_buffer = []
        
        if WHISPER_AVAILABLE:
            try:
                print(f"Loading Whisper model: {model_size}")
                self.model = whisper.load_model(model_size)
                print("Whisper model loaded successfully")
            except Exception as e:
                print(f"Warning: Failed to load Whisper model: {e}")
                print("Falling back to placeholder transcription")
                self.model = None
        else:
            print("Whisper not available. Using placeholder transcription.")
    
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
            
            # Transcribe using Whisper
            result = self.model.transcribe(
                audio_array,
                language="en",
                task="transcribe",
                fp16=False,
                verbose=False
            )
            
            return result.get("text", "").strip()
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
            return f"[Placeholder transcription for {duration:.1f}s of audio. Install openai-whisper for real transcription.]"
        
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Transcribe using Whisper
            result = self.model.transcribe(
                audio_array,
                language="en",
                task="transcribe",
                fp16=False,
                verbose=False
            )
            
            return result.get("text", "").strip()
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

