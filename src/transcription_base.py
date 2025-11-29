from abc import ABC, abstractmethod
from typing import Optional


class TranscriberBase(ABC):
    """Abstract base class for speech-to-text transcription providers."""

    def __init__(self, api_key: str | None, provider_name: str):
        """
        Initialize the transcriber with API key validation.

        Args:
            api_key: API key for the transcription service
            provider_name: Name of the provider (for error messages)

        Raises:
            ValueError: If API key is not provided
        """
        if not api_key:
            raise ValueError(
                f"{provider_name} API key is required. Set {provider_name.upper()}_API_KEY "
                f"environment variable or pass api_key parameter."
            )
        self.api_key = api_key

    @abstractmethod
    def transcribe_audio(
        self, audio_file_path: str, language: Optional[str] = None
    ) -> Optional[str]:
        """
        Transcribe audio file to text.

        Args:
            audio_file_path: Path to the audio file
            language: Language code (optional, auto-detect if None)

        Returns:
            Transcribed text or None if transcription failed
        """
        pass
