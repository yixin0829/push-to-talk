import os
from loguru import logger
import time
import wave
from typing import Optional
from deepgram import DeepgramClient

from src.transcription_base import TranscriberBase


class DeepgramTranscriber(TranscriberBase):
    """Deepgram transcription implementation."""

    def __init__(self, api_key: Optional[str] = None, model: str = "nova-3"):
        """
        Initialize the transcriber with Deepgram API.

        Args:
            api_key: Deepgram API key. If None, will use DEEPGRAM_API_KEY environment variable
            model: STT Model to use (default: nova-3)
        """
        self.api_key = api_key or os.getenv("DEEPGRAM_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Deepgram API key is required. Set DEEPGRAM_API_KEY environment variable or pass api_key parameter."
            )

        self.model = model
        self.client = DeepgramClient(api_key=self.api_key)

    def transcribe_audio(
        self, audio_file_path: str, language: Optional[str] = None
    ) -> Optional[str]:
        """
        Transcribe audio file to text using Deepgram API.

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

            # Read audio file
            with open(audio_file_path, "rb") as audio_file:
                audio_data = audio_file.read()

            # Build transcription options
            options = {
                "model": self.model,
                "smart_format": True,  # Enable smart formatting for better readability
            }

            # Add language if specified
            if language:
                options["language"] = language

            # Call Deepgram API
            response = self.client.listen.v1.media.transcribe_file(
                request=audio_data, **options
            )

            # Extract transcript from response
            # Deepgram response structure: response.results.channels[0].alternatives[0].transcript
            if (
                hasattr(response, "results")
                and hasattr(response.results, "channels")
                and len(response.results.channels) > 0
            ):
                channel = response.results.channels[0]
                if hasattr(channel, "alternatives") and len(channel.alternatives) > 0:
                    transcribed_text = channel.alternatives[0].transcript
                else:
                    logger.warning("No alternatives found in Deepgram response")
                    return None
            else:
                logger.warning("Invalid Deepgram response structure")
                return None

            transcribed_text = transcribed_text.strip()
            transcription_time = time.time() - start_time

            logger.info(
                f"Transcription successful: {len(transcribed_text)} characters in {transcription_time:.2f}s"
            )
            return transcribed_text if transcribed_text else None

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None
