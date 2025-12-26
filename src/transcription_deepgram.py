import os
from loguru import logger
import time
from typing import Optional, List
from deepgram import DeepgramClient

from src.transcription_base import TranscriberBase
from src.utils import validate_audio_file_exists, validate_audio_duration


class DeepgramTranscriber(TranscriberBase):
    """Deepgram transcription implementation."""

    # Approximate token limit for keyterms (Deepgram's limit is 500 tokens)
    # We use a conservative estimate of ~100 characters per 20 tokens
    MAX_KEYTERM_CHARS = 2000  # Conservative limit to stay under 500 tokens

    def __init__(self, api_key: Optional[str] = None, model: str = "nova-3"):
        """
        Initialize the transcriber with Deepgram API.

        Args:
            api_key: Deepgram API key. If None, will use DEEPGRAM_API_KEY environment variable
            model: STT Model to use (default: nova-3)
        """
        api_key = api_key or os.getenv("DEEPGRAM_API_KEY")
        super().__init__(api_key, "Deepgram")

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

            # Build transcription options
            options = {
                "model": self.model,
                "smart_format": True,  # Enable smart formatting for better readability
            }

            # Add language if specified
            if language:
                options["language"] = language

            # Add keyterm prompting if glossary is provided and model supports it
            if self.glossary and self.model in ["nova-3"]:
                # Prepare keyterms, limiting total character count to stay under token limit
                keyterms = self._prepare_keyterms(self.glossary)
                if keyterms:
                    options["keyterm"] = keyterms
                    logger.debug(f"Using {len(keyterms)} keyterms for transcription")
            else:
                logger.debug(
                    "No keyterms provided or model not supported. Only support nova-3 model for keyterms."
                )

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

    def _prepare_keyterms(self, glossary: List[str]) -> List[str]:
        """
        Prepare keyterms from glossary, limiting to stay under token limit.

        Args:
            glossary: List of custom terms/phrases

        Returns:
            List of keyterms to use, limited by token count
        """
        if not glossary:
            return []

        keyterms = []
        total_chars = 0

        for term in glossary:
            term_length = len(term)
            if total_chars + term_length + 1 > self.MAX_KEYTERM_CHARS:
                logger.warning(
                    f"Keyterm limit reached. Using first {len(keyterms)} of {len(glossary)} glossary terms"
                )
                break

            keyterms.append(term)
            total_chars += term_length + 1  # +1 for separator

        return keyterms
