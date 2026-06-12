import os
from loguru import logger
import time
from typing import Optional, List

import httpx

from src.transcription_base import TranscriberBase
from src.utils import validate_audio_file_exists, validate_audio_duration
from src.exceptions import TranscriptionError, APIError


class SixtyDBTranscriber(TranscriberBase):
    """60dB (60db.ai) speech-to-text transcription implementation.

    Unlike OpenAI/Deepgram, 60dB does not publish a Python SDK, so this talks
    to the REST endpoint directly via httpx. The 60dB STT endpoint also has no
    notion of a selectable model, so the ``model`` argument is accepted for
    interface consistency but is not sent to the API.
    """

    # 60dB API base URL and speech-to-text endpoint
    BASE_URL = "https://api.60db.ai"
    STT_ENDPOINT = "/stt"

    # Default keyword boost weight (60dB accepts 1.5-10; the docs example uses 5)
    DEFAULT_KEYWORD_WEIGHT = 5

    # Conservative character budget for the keywords field to keep requests small.
    # Mirrors the keyterm budgeting used by the Deepgram transcriber.
    MAX_KEYWORD_CHARS = 2000

    # Request timeout in seconds (60dB allows up to 1 hour / 10 MB audio)
    REQUEST_TIMEOUT = 60.0

    def __init__(self, api_key: Optional[str] = None, model: str = "60db-stt"):
        """
        Initialize the transcriber with the 60dB API.

        Args:
            api_key: 60dB API key. If None, will use the SIXTYDB_API_KEY
                environment variable.
            model: Placeholder STT model name. 60dB's STT endpoint does not take
                a model parameter; this is kept for interface consistency.
        """
        api_key = api_key or os.getenv("SIXTYDB_API_KEY")
        super().__init__(api_key, "60dB")

        self.model = model

    def transcribe_audio(
        self, audio_file_path: str, language: Optional[str] = None
    ) -> Optional[str]:
        """
        Transcribe audio file to text using the 60dB API.

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

            # Read audio file
            with open(audio_file_path, "rb") as audio_file:
                audio_data = audio_file.read()

            # Build multipart form fields
            data = {}

            # Add language if specified (60dB auto-detects when omitted)
            if language:
                data["language"] = language

            # Map custom glossary to 60dB keyword boosting
            if self.glossary:
                keywords = self._prepare_keywords(self.glossary)
                if keywords:
                    data["keywords"] = keywords
                    logger.debug(f"Using keyword boost: {keywords}")

            files = {
                "file": (
                    os.path.basename(audio_file_path),
                    audio_data,
                    "audio/wav",
                )
            }
            headers = {"Authorization": f"Bearer {self.api_key}"}

            # Call 60dB STT API
            response = httpx.post(
                f"{self.BASE_URL}{self.STT_ENDPOINT}",
                files=files,
                data=data,
                headers=headers,
                timeout=self.REQUEST_TIMEOUT,
            )
            response.raise_for_status()

            # Extract transcript from response
            # 60dB response structure: {"text": "...", "language": "...", ...}
            result = response.json()
            transcribed_text = result.get("text")
            if transcribed_text is None:
                logger.warning("Invalid 60dB response structure: missing 'text'")
                return None

            transcribed_text = transcribed_text.strip()
            transcription_time = time.time() - start_time

            logger.info(
                f"Transcription successful: {len(transcribed_text)} characters in {transcription_time:.2f}s"
            )
            return transcribed_text if transcribed_text else None

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            logger.error(f"60dB API error during transcription: {e}")
            raise APIError(
                f"60dB transcription API failed: {e}",
                provider="60dB",
                status_code=status_code,
            ) from e
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise TranscriptionError(f"Failed to transcribe audio: {e}") from e

    def _prepare_keywords(self, glossary: List[str]) -> str:
        """
        Prepare a 60dB keywords string from the glossary.

        60dB expects a comma-separated list of ``term:weight`` pairs (weights
        1.5-10). Terms are added until the character budget is reached.

        Args:
            glossary: List of custom terms/phrases

        Returns:
            Comma-separated ``term:weight`` string (empty if no glossary)
        """
        if not glossary:
            return ""

        entries = []
        total_chars = 0

        for term in glossary:
            entry = f"{term}:{self.DEFAULT_KEYWORD_WEIGHT}"
            # +1 accounts for the comma separator between entries
            if total_chars + len(entry) + 1 > self.MAX_KEYWORD_CHARS:
                logger.warning(
                    f"Keyword limit reached. Using first {len(entries)} of {len(glossary)} glossary terms"
                )
                break

            entries.append(entry)
            total_chars += len(entry) + 1

        return ",".join(entries)
