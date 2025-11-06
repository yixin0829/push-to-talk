import os
from loguru import logger
import time
import wave
from typing import Optional
import litellm


class Transcriber:
    def __init__(
        self,
        provider: str = "openai",
        model: str = "whisper-1",
        openai_api_key: Optional[str] = None,
        deepgram_api_key: Optional[str] = None,
        elevenlabs_api_key: Optional[str] = None,
        custom_stt_url: Optional[str] = None,
        custom_stt_api_key: Optional[str] = None,
    ):
        """
        Initialize the transcriber with support for multiple STT providers.

        Args:
            provider: STT provider to use (openai, deepgram, elevenlabs, custom)
            model: STT Model to use (default: whisper-1)
            openai_api_key: OpenAI API key
            deepgram_api_key: Deepgram API key
            elevenlabs_api_key: ElevenLabs API key
            custom_stt_url: Custom STT endpoint URL
            custom_stt_api_key: Custom STT API key
        """
        self.provider = provider
        self.model = model

        # Set environment variables for LiteLLM based on provider
        if provider == "openai":
            api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass openai_api_key parameter."
                )
            os.environ["OPENAI_API_KEY"] = api_key
            # For OpenAI, use model name directly
            self.model_name = model
        elif provider == "deepgram":
            api_key = deepgram_api_key or os.getenv("DEEPGRAM_API_KEY")
            if not api_key:
                raise ValueError(
                    "Deepgram API key is required. Set DEEPGRAM_API_KEY environment variable or pass deepgram_api_key parameter."
                )
            os.environ["DEEPGRAM_API_KEY"] = api_key
            # For Deepgram, prefix model with provider name
            self.model_name = f"deepgram/{model}" if not model.startswith("deepgram/") else model
        elif provider == "elevenlabs":
            api_key = elevenlabs_api_key or os.getenv("ELEVENLABS_API_KEY")
            if not api_key:
                raise ValueError(
                    "ElevenLabs API key is required. Set ELEVENLABS_API_KEY environment variable or pass elevenlabs_api_key parameter."
                )
            os.environ["ELEVENLABS_API_KEY"] = api_key
            # For ElevenLabs, prefix model with provider name
            self.model_name = f"elevenlabs/{model}" if not model.startswith("elevenlabs/") else model
        elif provider == "custom":
            if not custom_stt_url:
                raise ValueError("Custom STT URL is required for custom provider.")
            self.custom_url = custom_stt_url
            self.custom_api_key = custom_stt_api_key or ""
            self.model_name = model
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        logger.info(f"Initialized transcriber with provider: {provider}, model: {self.model_name}")

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
                # Use LiteLLM for transcription across all providers
                if self.provider == "custom":
                    # For custom provider, use litellm with custom URL
                    response = litellm.transcription(
                        model=self.model_name,
                        file=audio_file,
                        api_base=self.custom_url,
                        api_key=self.custom_api_key,
                    )
                else:
                    # For standard providers (OpenAI, Deepgram, ElevenLabs)
                    response = litellm.transcription(
                        model=self.model_name,
                        file=audio_file,
                        language=language,
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
                f"Transcription successful ({self.provider}): {len(transcribed_text)} characters in {transcription_time:.2f}s"
            )
            return transcribed_text if transcribed_text else None

        except Exception as e:
            logger.error(f"Transcription failed ({self.provider}): {e}")
            return None
