import os
from loguru import logger
import time
import wave
from typing import Optional
from openai import OpenAI


class Transcriber:
    def __init__(self, api_key: Optional[str] = None, model: str = "whisper-1"):
        """
        Initialize the transcriber with OpenAI API.

        Args:
            api_key: OpenAI API key. If None, will use OPENAI_API_KEY environment variable
            model: STT Model to use (default: whisper-1)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter."
            )

        self.model = model
        self.client = OpenAI(api_key=self.api_key)

    def transcribe_audio(
        self, audio_file_path: str, language: Optional[str] = None
    ) -> Optional[str]:
        """
        Transcribe audio file to text using OpenAI API.

        Args:
            audio_file_path: Path to the audio file
            language: Language code (optional, auto-detect if None)

        Returns:
            Transcribed text or None if transcription failed
        """
        if not os.path.exists(audio_file_path):
            logger.error(f"Audio file not found: {audio_file_path}")
            return None

        # Skip very short audio clips (< 0.5s) to avoid unnecessary API calls
        try:
            with wave.open(audio_file_path, "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate() or 0
                duration_seconds = frames / float(rate) if rate else 0.0
            if duration_seconds < 0.5:
                logger.info(
                    f"Audio too short ({duration_seconds:.3f}s); skipping transcription"
                )
                return None
        except Exception as e:
            # If duration cannot be determined (e.g., not a valid WAV), handle it gracefully
            logger.debug(
                f"Could not determine audio duration for {audio_file_path}: {e}"
            )

        try:
            start_time = time.time()
            logger.debug(f"Starting transcription for: {audio_file_path}")

            with open(audio_file_path, "rb") as audio_file:
                response = self.client.audio.transcriptions.create(
                    model=self.model,
                    file=audio_file,
                    language=language,
                    response_format="text",
                )

            # Handle both string and object responses
            if hasattr(response, "text"):
                transcribed_text = response.text
            elif isinstance(response, str):
                transcribed_text = response
            else:
                # Fallback to string representation
                logger.warning(
                    "Unknown transcription response format, using string representation"
                )
                transcribed_text = str(response)

            transcribed_text = transcribed_text.strip()
            transcription_time = time.time() - start_time

            logger.info(
                f"Transcription successful: {len(transcribed_text)} characters in {transcription_time:.2f}s"
            )
            return transcribed_text if transcribed_text else None

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None
