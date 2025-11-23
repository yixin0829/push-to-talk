from src.transcription_base import TranscriberBase
from src.transcription_openai import OpenAITranscriber
from src.transcription_deepgram import DeepgramTranscriber


class TranscriberFactory:
    """Factory for creating transcriber instances based on provider."""

    @staticmethod
    def create_transcriber(
        provider: str,
        api_key: str,
        model: str,
    ) -> TranscriberBase:
        """
        Create and return a transcriber instance.

        Args:
            provider: The transcription provider ("openai" or "deepgram")
            api_key: API key for the selected provider
            model: Model name to use for transcription

        Returns:
            TranscriberBase instance for the selected provider

        Raises:
            ValueError: If an unknown provider is specified
        """
        if provider == "openai":
            return OpenAITranscriber(api_key=api_key, model=model)
        elif provider == "deepgram":
            return DeepgramTranscriber(api_key=api_key, model=model)
        else:
            raise ValueError(f"Unknown transcription provider: {provider}")
