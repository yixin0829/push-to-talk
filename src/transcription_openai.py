import os
from loguru import logger
import time
from typing import Optional
from openai import OpenAI

from src.transcription_base import TranscriberBase
from src.utils import validate_audio_file_exists, validate_audio_duration


class OpenAITranscriber(TranscriberBase):
    def __init__(self, api_key: Optional[str] = None, model: str = "whisper-1"):
        """
        Initialize the transcriber with OpenAI API.

        Args:
            api_key: OpenAI API key. If None, will use OPENAI_API_KEY environment variable
            model: STT Model to use (default: whisper-1)
        """
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        super().__init__(api_key, "OpenAI")

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
        # Validate file exists
        if not validate_audio_file_exists(audio_file_path):
            return None

        # Validate audio duration
        if not validate_audio_duration(audio_file_path):
            return None

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
