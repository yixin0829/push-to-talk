import pytest
import os
from loguru import logger
from unittest.mock import MagicMock

from src.transcription_openai import OpenAITranscriber
from src.exceptions import ConfigurationError, TranscriptionError, APIError


class TestOpenAITranscriber:
    @pytest.fixture(autouse=True)
    def setup(self, mocker):
        """Setup for each test method"""
        logger.info("Setting up OpenAITranscriber test")

        # Use a mock API key for testing
        mocker.patch.dict(os.environ, {"OPENAI_API_KEY": "test-api-key"})
        self.transcriber = OpenAITranscriber()

    def test_initialization_with_env_var(self, mocker):
        """Test OpenAITranscriber initialization with environment variable"""
        logger.info("Testing OpenAITranscriber initialization with env var")

        mocker.patch.dict(os.environ, {"OPENAI_API_KEY": "env-api-key"})
        transcriber = OpenAITranscriber()

        assert transcriber.api_key == "env-api-key"
        assert transcriber.model == "whisper-1"
        assert transcriber.client is not None

        logger.info("OpenAITranscriber initialization with env var test passed")

    def test_initialization_with_explicit_key(self):
        """Test OpenAITranscriber initialization with explicit API key"""
        logger.info("Testing OpenAITranscriber initialization with explicit key")

        transcriber = OpenAITranscriber(
            api_key="explicit-api-key", model="custom-model"
        )

        assert transcriber.api_key == "explicit-api-key"
        assert transcriber.model == "custom-model"
        assert transcriber.client is not None

        logger.info("OpenAITranscriber initialization with explicit key test passed")

    def test_initialization_no_api_key(self, mocker):
        """Test OpenAITranscriber initialization without API key"""
        logger.info("Testing OpenAITranscriber initialization without API key")

        mocker.patch.dict(os.environ, {}, clear=True)
        with pytest.raises(ConfigurationError) as exc_info:
            OpenAITranscriber()

        assert "OpenAI API key is required" in str(exc_info.value)

        logger.info("OpenAITranscriber initialization no API key test passed")

    def test_transcribe_audio_success(self, mocker):
        """Test successful audio transcription"""
        logger.info("Testing successful audio transcription")

        mocker.patch("builtins.open", mocker.mock_open(read_data=b"fake audio data"))
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.remove")

        # Mock the OpenAI client response
        mock_response = "This is the transcribed text."
        self.transcriber.client.audio.transcriptions.create = MagicMock(
            return_value=mock_response
        )

        result = self.transcriber.transcribe_audio("test_audio.wav")

        assert result == "This is the transcribed text."

        # Verify the API was called correctly
        self.transcriber.client.audio.transcriptions.create.assert_called_once()
        call_args = self.transcriber.client.audio.transcriptions.create.call_args
        assert call_args[1]["model"] == "whisper-1"
        assert call_args[1]["response_format"] == "text"

        logger.info("Transcribe audio success test passed")

    def test_transcribe_audio_with_language(self, mocker):
        """Test audio transcription with language specified"""
        logger.info("Testing audio transcription with language")

        mocker.patch("builtins.open", mocker.mock_open(read_data=b"fake audio data"))
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.remove")

        mock_response = "This is transcribed French text."
        self.transcriber.client.audio.transcriptions.create = MagicMock(
            return_value=mock_response
        )

        result = self.transcriber.transcribe_audio("test_audio.wav", language="fr")

        assert result == "This is transcribed French text."

        # Verify language parameter was passed
        call_args = self.transcriber.client.audio.transcriptions.create.call_args
        assert call_args[1]["language"] == "fr"

        logger.info("Transcribe audio with language test passed")

    def test_transcribe_audio_file_not_found(self, mocker):
        """Test transcription when audio file doesn't exist"""
        logger.info("Testing transcription with missing file")

        mocker.patch("os.path.exists", return_value=False)

        result = self.transcriber.transcribe_audio("nonexistent.wav")

        assert result is None

        logger.info("Transcribe audio file not found test passed")

    def test_transcribe_audio_api_failure(self, mocker):
        """Test transcription API failure raises TranscriptionError"""
        logger.info("Testing transcription API failure")

        mocker.patch("builtins.open", mocker.mock_open(read_data=b"fake audio data"))
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.remove")

        # Mock API failure (generic exception)
        self.transcriber.client.audio.transcriptions.create = MagicMock(
            side_effect=Exception("API request failed")
        )

        with pytest.raises(TranscriptionError, match="Failed to transcribe audio"):
            self.transcriber.transcribe_audio("test_audio.wav")

        logger.info("Transcribe audio API failure test passed")

    def test_transcribe_audio_empty_response(self, mocker):
        """Test transcription with empty response"""
        logger.info("Testing transcription with empty response")

        mocker.patch("builtins.open", mocker.mock_open(read_data=b"fake audio data"))
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.remove")

        # Mock empty response
        self.transcriber.client.audio.transcriptions.create = MagicMock(return_value="")

        result = self.transcriber.transcribe_audio("test_audio.wav")

        assert result is None

        logger.info("Transcribe audio empty response test passed")

    def test_transcribe_audio_whitespace_response(self, mocker):
        """Test transcription with whitespace-only response"""
        logger.info("Testing transcription with whitespace response")

        mocker.patch("builtins.open", mocker.mock_open(read_data=b"fake audio data"))
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.remove")

        # Mock whitespace response
        self.transcriber.client.audio.transcriptions.create = MagicMock(
            return_value="   \n  \t  "
        )

        result = self.transcriber.transcribe_audio("test_audio.wav")

        assert result is None

        logger.info("Transcribe audio whitespace response test passed")

    def test_transcribe_audio_object_response(self, mocker):
        """Test transcription with object response (has text attribute)"""
        logger.info("Testing transcription with object response")

        mocker.patch("builtins.open", mocker.mock_open(read_data=b"fake audio data"))
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.remove")

        # Mock object response with text attribute
        mock_response = MagicMock()
        mock_response.text = "Transcribed text from object"
        self.transcriber.client.audio.transcriptions.create = MagicMock(
            return_value=mock_response
        )

        result = self.transcriber.transcribe_audio("test_audio.wav")

        assert result == "Transcribed text from object"

        logger.info("Transcribe audio object response test passed")

    def test_transcribe_audio_object_without_text(self, mocker):
        """Test transcription with object response without text attribute"""
        logger.info("Testing transcription with object response without text")

        mocker.patch("builtins.open", mocker.mock_open(read_data=b"fake audio data"))
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.remove")

        # Mock object response without text attribute
        mock_response = MagicMock()
        del mock_response.text  # Remove text attribute
        mock_response.__str__ = MagicMock(return_value="String representation")
        self.transcriber.client.audio.transcriptions.create = MagicMock(
            return_value=mock_response
        )

        result = self.transcriber.transcribe_audio("test_audio.wav")

        assert result == "String representation"

        logger.info("Transcribe audio object without text test passed")

    def test_transcribe_audio_timing(self, mocker):
        """Test transcription timing measurement"""
        logger.info("Testing transcription timing measurement")

        mocker.patch("builtins.open", mocker.mock_open(read_data=b"fake audio data"))
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.remove")

        # Mock time progression - need more calls for logging
        mock_time = mocker.patch("time.time")
        mock_time.side_effect = [1000.0, 1002.5, 1002.6, 1002.7, 1002.8, 1002.9]

        mock_response = "Timed transcription"
        self.transcriber.client.audio.transcriptions.create = MagicMock(
            return_value=mock_response
        )

        result = self.transcriber.transcribe_audio("test_audio.wav")

        assert result == "Timed transcription"

        # Verify time.time() was called at least twice (start and end)
        assert mock_time.call_count >= 2

        logger.info("Transcribe audio timing test passed")

    def test_transcribe_audio_cleanup_failure(self, mocker):
        """Test transcription when cleanup fails"""
        logger.info("Testing transcription cleanup failure")

        mocker.patch("builtins.open", mocker.mock_open(read_data=b"fake audio data"))
        mocker.patch("os.path.exists", return_value=True)

        # Mock cleanup failure
        mock_remove = mocker.patch("os.remove")
        mock_remove.side_effect = Exception("Failed to remove file")

        mock_response = "Transcription despite cleanup failure"
        self.transcriber.client.audio.transcriptions.create = MagicMock(
            return_value=mock_response
        )

        result = self.transcriber.transcribe_audio("test_audio.wav")

        # Should still return successful transcription despite cleanup failure
        assert result == "Transcription despite cleanup failure"

        logger.info("Transcribe audio cleanup failure test passed")

    def test_transcribe_audio_openai_api_error(self, mocker):
        """Test that OpenAI API errors raise APIError"""
        logger.info("Testing OpenAI API error handling")

        mocker.patch("builtins.open", mocker.mock_open(read_data=b"fake audio data"))
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.remove")

        # Import OpenAI's APIError to mock it
        from openai import APIError as OpenAIAPIError

        # Mock OpenAI API error with status_code
        api_error = OpenAIAPIError("API rate limit exceeded", response=None, body=None)
        api_error.status_code = 429
        self.transcriber.client.audio.transcriptions.create = MagicMock(
            side_effect=api_error
        )

        with pytest.raises(APIError, match="OpenAI transcription API failed"):
            self.transcriber.transcribe_audio("test_audio.wav")

        logger.info("OpenAI API error test passed")

    def test_different_model_initialization(self, mocker):
        """Test initialization with different model"""
        logger.info("Testing initialization with different model")

        mocker.patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
        transcriber = OpenAITranscriber(model="whisper-large")

        assert transcriber.model == "whisper-large"

        logger.info("Different model initialization test passed")

    def test_transcribe_audio_with_custom_model(self, mocker):
        """Test transcription with custom model"""
        logger.info("Testing transcription with custom model")

        mocker.patch("builtins.open", mocker.mock_open(read_data=b"fake audio data"))
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.remove")

        # Create transcriber with custom model
        mocker.patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
        transcriber = OpenAITranscriber(model="whisper-large")

        mock_response = "Custom model transcription"
        transcriber.client.audio.transcriptions.create = MagicMock(
            return_value=mock_response
        )

        result = transcriber.transcribe_audio("test_audio.wav")

        assert result == "Custom model transcription"

        # Verify custom model was used
        call_args = transcriber.client.audio.transcriptions.create.call_args
        assert call_args[1]["model"] == "whisper-large"

        logger.info("Transcribe audio with custom model test passed")
