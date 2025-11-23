from abc import ABC, abstractmethod
from typing import Optional


class TranscriberBase(ABC):
    """Abstract base class for speech-to-text transcription providers."""

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
