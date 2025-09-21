from typing import Optional, Union
from loguru import logger

from src.transcription import Transcriber
from src.local_whisper_transcriber import LocalWhisperTranscriber


class TranscriberFactory:
    """Factory for creating transcriber instances based on configuration."""

    # OpenAI API model names
    OPENAI_MODELS = {"whisper-1", "gpt-4o-transcribe", "gpt-4o-mini-transcribe"}

    # Local Whisper model names
    LOCAL_WHISPER_MODELS = {
        "tiny.en",
        "tiny",
        "base.en",
        "base",
        "small.en",
        "small",
        "medium.en",
        "medium",
        "large-v1",
        "large-v2",
        "large-v3",
        "large-v3-turbo",
    }

    @staticmethod
    def create_transcriber(
        model_name: str,
        use_local_whisper: bool = False,
        openai_api_key: Optional[str] = None,
        local_whisper_device: str = "auto",
        local_whisper_compute_type: str = "auto",
    ) -> Union[Transcriber, LocalWhisperTranscriber]:
        """
        Create a transcriber instance based on configuration.

        Args:
            model_name: Name of the model to use
            use_local_whisper: Whether to use local Whisper instead of OpenAI API
            openai_api_key: OpenAI API key (required for API models)
            local_whisper_device: Device for local whisper ("auto", "cpu", "cuda")
            local_whisper_compute_type: Compute type for local whisper ("auto", "float16", "int8", "float32")

        Returns:
            Appropriate transcriber instance

        Raises:
            ValueError: If invalid configuration or missing requirements
        """
        logger.info(
            f"Creating transcriber: model={model_name}, local={use_local_whisper}"
        )

        if use_local_whisper:
            return TranscriberFactory._create_local_whisper_transcriber(
                model_name, local_whisper_device, local_whisper_compute_type
            )
        else:
            return TranscriberFactory._create_openai_transcriber(
                model_name, openai_api_key
            )

    @staticmethod
    def _create_local_whisper_transcriber(
        model_name: str, device: str, compute_type: str
    ) -> LocalWhisperTranscriber:
        """Create a local Whisper transcriber."""
        if not LocalWhisperTranscriber.is_available():
            raise ValueError(
                "pywhispercpp is not installed. Please install it with: pip install pywhispercpp"
            )

        # Validate model name for local Whisper
        if model_name not in TranscriberFactory.LOCAL_WHISPER_MODELS:
            logger.warning(
                f"Model '{model_name}' not in known local models. "
                f"Supported models: {', '.join(TranscriberFactory.LOCAL_WHISPER_MODELS)}"
            )

        try:
            transcriber = LocalWhisperTranscriber(
                model_name=model_name, device=device, compute_type=compute_type
            )
            logger.info(f"Created LocalWhisperTranscriber with model '{model_name}'")
            return transcriber
        except Exception as e:
            logger.error(f"Failed to create LocalWhisperTranscriber: {e}")
            raise ValueError(
                f"Failed to initialize local Whisper model '{model_name}': {e}"
            )

    @staticmethod
    def _create_openai_transcriber(
        model_name: str, api_key: Optional[str]
    ) -> Transcriber:
        """Create an OpenAI API transcriber."""
        if not api_key:
            raise ValueError("OpenAI API key is required for API-based transcription")

        # Validate model name for OpenAI API
        if model_name not in TranscriberFactory.OPENAI_MODELS:
            logger.warning(
                f"Model '{model_name}' not in known OpenAI models. "
                f"Supported models: {', '.join(TranscriberFactory.OPENAI_MODELS)}"
            )

        try:
            transcriber = Transcriber(api_key=api_key, model=model_name)
            logger.info(f"Created OpenAI Transcriber with model '{model_name}'")
            return transcriber
        except Exception as e:
            logger.error(f"Failed to create OpenAI Transcriber: {e}")
            raise ValueError(f"Failed to initialize OpenAI transcriber: {e}")

    @staticmethod
    def is_local_model(model_name: str) -> bool:
        """Check if a model name corresponds to a local Whisper model."""
        return model_name in TranscriberFactory.LOCAL_WHISPER_MODELS

    @staticmethod
    def is_openai_model(model_name: str) -> bool:
        """Check if a model name corresponds to an OpenAI API model."""
        return model_name in TranscriberFactory.OPENAI_MODELS

    @staticmethod
    def get_available_models() -> dict:
        """Get all available models categorized by type."""
        return {
            "openai_api": sorted(TranscriberFactory.OPENAI_MODELS),
            "local_whisper": sorted(TranscriberFactory.LOCAL_WHISPER_MODELS),
        }

    @staticmethod
    def validate_configuration(
        model_name: str, use_local_whisper: bool, openai_api_key: Optional[str] = None
    ) -> tuple[bool, str]:
        """
        Validate transcriber configuration.

        Args:
            model_name: Name of the model
            use_local_whisper: Whether using local whisper
            openai_api_key: OpenAI API key

        Returns:
            Tuple of (is_valid, error_message)
        """
        if use_local_whisper:
            if not LocalWhisperTranscriber.is_available():
                return False, "pywhispercpp is not installed"

            if model_name not in TranscriberFactory.LOCAL_WHISPER_MODELS:
                return False, f"Unknown local Whisper model: {model_name}"

        else:
            if not openai_api_key:
                return False, "OpenAI API key is required for API models"

            if model_name not in TranscriberFactory.OPENAI_MODELS:
                return False, f"Unknown OpenAI model: {model_name}"

        return True, ""
