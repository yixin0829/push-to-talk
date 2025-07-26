import os
import logging
from typing import Optional
from openai import OpenAI
import tempfile

logger = logging.getLogger(__name__)

class Transcriber:
    def __init__(self, api_key: Optional[str] = None, model: str = "whisper-1"):
        """
        Initialize the transcriber with OpenAI API.
        
        Args:
            api_key: OpenAI API key. If None, will use OPENAI_API_KEY environment variable
            model: Whisper model to use (default: whisper-1)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        self.model = model
        self.client = OpenAI(api_key=self.api_key)
        
    def transcribe_audio(self, audio_file_path: str, language: Optional[str] = None) -> Optional[str]:
        """
        Transcribe audio file to text using OpenAI Whisper.
        
        Args:
            audio_file_path: Path to the audio file
            language: Language code (optional, auto-detect if None)
            
        Returns:
            Transcribed text or None if transcription failed
        """
        if not os.path.exists(audio_file_path):
            logger.error(f"Audio file not found: {audio_file_path}")
            return None
            
        try:
            with open(audio_file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model=self.model,
                    file=audio_file,
                    language=language,
                    response_format="text"
                )
            
            # Clean up temporary file
            try:
                os.unlink(audio_file_path)
                logger.debug(f"Cleaned up temporary audio file: {audio_file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up audio file {audio_file_path}: {e}")
            
            if isinstance(transcript, str):
                text = transcript.strip()
            else:
                text = transcript.text.strip() if hasattr(transcript, 'text') else str(transcript).strip()
            
            logger.info(f"Transcription successful: {len(text)} characters")
            return text if text else None
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            # Clean up temporary file even on error
            try:
                if os.path.exists(audio_file_path):
                    os.unlink(audio_file_path)
            except:
                pass
            return None 