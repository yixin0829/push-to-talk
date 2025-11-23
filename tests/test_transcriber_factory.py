import pytest
from loguru import logger

from src.transcriber_factory import TranscriberFactory
from src.transcription_openai import OpenAITranscriber
from src.transcription_deepgram import DeepgramTranscriber
from src.transcription_base import TranscriberBase


class TestTranscriberFactory:
    def test_create_openai_transcriber(self):
        """Test factory creates OpenAI transcriber"""
        logger.info("Testing factory creates OpenAI transcriber")

        transcriber = TranscriberFactory.create_transcriber(
            provider="openai", api_key="test-openai-key", model="whisper-1"
        )

        assert isinstance(transcriber, OpenAITranscriber)
        assert isinstance(transcriber, TranscriberBase)
        assert transcriber.api_key == "test-openai-key"
        assert transcriber.model == "whisper-1"

        logger.info("Factory creates OpenAI transcriber test passed")

    def test_create_openai_transcriber_with_custom_model(self):
        """Test factory creates OpenAI transcriber with custom model"""
        logger.info("Testing factory creates OpenAI transcriber with custom model")

        transcriber = TranscriberFactory.create_transcriber(
            provider="openai", api_key="test-key", model="gpt-4o-transcribe"
        )

        assert isinstance(transcriber, OpenAITranscriber)
        assert transcriber.model == "gpt-4o-transcribe"

        logger.info("Factory creates OpenAI transcriber with custom model test passed")

    def test_create_deepgram_transcriber(self):
        """Test factory creates Deepgram transcriber"""
        logger.info("Testing factory creates Deepgram transcriber")

        transcriber = TranscriberFactory.create_transcriber(
            provider="deepgram", api_key="test-deepgram-key", model="nova-3"
        )

        assert isinstance(transcriber, DeepgramTranscriber)
        assert isinstance(transcriber, TranscriberBase)
        assert transcriber.api_key == "test-deepgram-key"
        assert transcriber.model == "nova-3"

        logger.info("Factory creates Deepgram transcriber test passed")

    def test_create_deepgram_transcriber_with_custom_model(self):
        """Test factory creates Deepgram transcriber with custom model"""
        logger.info("Testing factory creates Deepgram transcriber with custom model")

        transcriber = TranscriberFactory.create_transcriber(
            provider="deepgram", api_key="test-key", model="base"
        )

        assert isinstance(transcriber, DeepgramTranscriber)
        assert transcriber.model == "base"

        logger.info(
            "Factory creates Deepgram transcriber with custom model test passed"
        )

    def test_invalid_provider_raises_error(self):
        """Test invalid provider raises ValueError"""
        logger.info("Testing invalid provider raises ValueError")

        with pytest.raises(ValueError) as exc_info:
            TranscriberFactory.create_transcriber(
                provider="invalid", api_key="test-key", model="test-model"
            )

        assert "Unknown transcription provider" in str(exc_info.value)
        assert "invalid" in str(exc_info.value)

        logger.info("Invalid provider raises error test passed")

    def test_empty_provider_raises_error(self):
        """Test empty provider raises ValueError"""
        logger.info("Testing empty provider raises ValueError")

        with pytest.raises(ValueError) as exc_info:
            TranscriberFactory.create_transcriber(
                provider="", api_key="test-key", model="test-model"
            )

        assert "Unknown transcription provider" in str(exc_info.value)

        logger.info("Empty provider raises error test passed")

    def test_case_sensitive_provider(self):
        """Test provider names are case-sensitive"""
        logger.info("Testing provider names are case-sensitive")

        # Should fail with uppercase
        with pytest.raises(ValueError):
            TranscriberFactory.create_transcriber(
                provider="OPENAI", api_key="test-key", model="whisper-1"
            )

        with pytest.raises(ValueError):
            TranscriberFactory.create_transcriber(
                provider="OpenAI", api_key="test-key", model="whisper-1"
            )

        logger.info("Case-sensitive provider test passed")

    def test_all_transcribers_implement_base_interface(self):
        """Test that all transcribers created by factory implement TranscriberBase"""
        logger.info("Testing all transcribers implement base interface")

        openai_transcriber = TranscriberFactory.create_transcriber(
            provider="openai", api_key="test-key", model="whisper-1"
        )

        deepgram_transcriber = TranscriberFactory.create_transcriber(
            provider="deepgram", api_key="test-key", model="nova-3"
        )

        # Check they all implement the base interface
        assert isinstance(openai_transcriber, TranscriberBase)
        assert isinstance(deepgram_transcriber, TranscriberBase)

        # Check they all have the transcribe_audio method
        assert hasattr(openai_transcriber, "transcribe_audio")
        assert hasattr(deepgram_transcriber, "transcribe_audio")
        assert callable(openai_transcriber.transcribe_audio)
        assert callable(deepgram_transcriber.transcribe_audio)

        logger.info("All transcribers implement base interface test passed")
