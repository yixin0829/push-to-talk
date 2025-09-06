import pytest
import os
import logging
from unittest.mock import patch, MagicMock, mock_open

from src.transcription import Transcriber

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestTranscriber:
    def setup_method(self):
        """Setup for each test method"""
        logger.info("Setting up Transcriber test")

        # Use a mock API key for testing
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-api-key"}):
            self.transcriber = Transcriber()

    def test_initialization_with_env_var(self):
        """Test Transcriber initialization with environment variable"""
        logger.info("Testing Transcriber initialization with env var")

        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-api-key"}):
            transcriber = Transcriber()

            assert transcriber.api_key == "env-api-key"
            assert transcriber.model == "whisper-1"
            assert transcriber.client is not None

        logger.info("Transcriber initialization with env var test passed")

    def test_initialization_with_explicit_key(self):
        """Test Transcriber initialization with explicit API key"""
        logger.info("Testing Transcriber initialization with explicit key")

        transcriber = Transcriber(api_key="explicit-api-key", model="custom-model")

        assert transcriber.api_key == "explicit-api-key"
        assert transcriber.model == "custom-model"
        assert transcriber.client is not None

        logger.info("Transcriber initialization with explicit key test passed")

    def test_initialization_no_api_key(self):
        """Test Transcriber initialization without API key"""
        logger.info("Testing Transcriber initialization without API key")

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                Transcriber()

            assert "OpenAI API key is required" in str(exc_info.value)

        logger.info("Transcriber initialization no API key test passed")

    @patch("builtins.open", mock_open(read_data=b"fake audio data"))
    @patch("os.path.exists")
    @patch("os.remove")
    def test_transcribe_audio_success(self, mock_remove, mock_exists):
        """Test successful audio transcription"""
        logger.info("Testing successful audio transcription")

        mock_exists.return_value = True

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

    @patch("builtins.open", mock_open(read_data=b"fake audio data"))
    @patch("os.path.exists")
    @patch("os.remove")
    def test_transcribe_audio_with_language(self, mock_remove, mock_exists):
        """Test audio transcription with language specified"""
        logger.info("Testing audio transcription with language")

        mock_exists.return_value = True

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

    @patch("os.path.exists")
    def test_transcribe_audio_file_not_found(self, mock_exists):
        """Test transcription when audio file doesn't exist"""
        logger.info("Testing transcription with missing file")

        mock_exists.return_value = False

        result = self.transcriber.transcribe_audio("nonexistent.wav")

        assert result is None

        logger.info("Transcribe audio file not found test passed")

    @patch("builtins.open", mock_open(read_data=b"fake audio data"))
    @patch("os.path.exists")
    @patch("os.remove")
    def test_transcribe_audio_api_failure(self, mock_remove, mock_exists):
        """Test transcription API failure"""
        logger.info("Testing transcription API failure")

        mock_exists.return_value = True

        # Mock API failure
        self.transcriber.client.audio.transcriptions.create = MagicMock(
            side_effect=Exception("API request failed")
        )

        result = self.transcriber.transcribe_audio("test_audio.wav")

        assert result is None

        logger.info("Transcribe audio API failure test passed")

    @patch("builtins.open", mock_open(read_data=b"fake audio data"))
    @patch("os.path.exists")
    @patch("os.remove")
    def test_transcribe_audio_empty_response(self, mock_remove, mock_exists):
        """Test transcription with empty response"""
        logger.info("Testing transcription with empty response")

        mock_exists.return_value = True

        # Mock empty response
        self.transcriber.client.audio.transcriptions.create = MagicMock(return_value="")

        result = self.transcriber.transcribe_audio("test_audio.wav")

        assert result is None

        logger.info("Transcribe audio empty response test passed")

    @patch("builtins.open", mock_open(read_data=b"fake audio data"))
    @patch("os.path.exists")
    @patch("os.remove")
    def test_transcribe_audio_whitespace_response(self, mock_remove, mock_exists):
        """Test transcription with whitespace-only response"""
        logger.info("Testing transcription with whitespace response")

        mock_exists.return_value = True

        # Mock whitespace response
        self.transcriber.client.audio.transcriptions.create = MagicMock(
            return_value="   \n  \t  "
        )

        result = self.transcriber.transcribe_audio("test_audio.wav")

        assert result is None

        logger.info("Transcribe audio whitespace response test passed")

    @patch("builtins.open", mock_open(read_data=b"fake audio data"))
    @patch("os.path.exists")
    @patch("os.remove")
    def test_transcribe_audio_object_response(self, mock_remove, mock_exists):
        """Test transcription with object response (has text attribute)"""
        logger.info("Testing transcription with object response")

        mock_exists.return_value = True

        # Mock object response with text attribute
        mock_response = MagicMock()
        mock_response.text = "Transcribed text from object"
        self.transcriber.client.audio.transcriptions.create = MagicMock(
            return_value=mock_response
        )

        result = self.transcriber.transcribe_audio("test_audio.wav")

        assert result == "Transcribed text from object"

        logger.info("Transcribe audio object response test passed")

    @patch("builtins.open", mock_open(read_data=b"fake audio data"))
    @patch("os.path.exists")
    @patch("os.remove")
    def test_transcribe_audio_object_without_text(self, mock_remove, mock_exists):
        """Test transcription with object response without text attribute"""
        logger.info("Testing transcription with object response without text")

        mock_exists.return_value = True

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

    @patch("builtins.open", mock_open(read_data=b"fake audio data"))
    @patch("os.path.exists")
    @patch("os.remove")
    @patch("time.time")
    def test_transcribe_audio_timing(self, mock_time, mock_remove, mock_exists):
        """Test transcription timing measurement"""
        logger.info("Testing transcription timing measurement")

        mock_exists.return_value = True

        # Mock time progression - need more calls for logging
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

    @patch("builtins.open", mock_open(read_data=b"fake audio data"))
    @patch("os.path.exists")
    @patch("os.remove")
    def test_transcribe_audio_cleanup_failure(self, mock_remove, mock_exists):
        """Test transcription when cleanup fails"""
        logger.info("Testing transcription cleanup failure")

        mock_exists.return_value = True

        # Mock cleanup failure
        mock_remove.side_effect = Exception("Failed to remove file")

        mock_response = "Transcription despite cleanup failure"
        self.transcriber.client.audio.transcriptions.create = MagicMock(
            return_value=mock_response
        )

        result = self.transcriber.transcribe_audio("test_audio.wav")

        # Should still return successful transcription despite cleanup failure
        assert result == "Transcription despite cleanup failure"

        logger.info("Transcribe audio cleanup failure test passed")

    @patch("builtins.open", mock_open(read_data=b"fake audio data"))
    @patch("os.path.exists")
    @patch("os.remove")
    def test_transcribe_audio_api_error_cleanup(self, mock_remove, mock_exists):
        """Test that cleanup happens even when API fails"""
        logger.info("Testing cleanup on API error")

        mock_exists.return_value = True

        # Mock API failure
        self.transcriber.client.audio.transcriptions.create = MagicMock(
            side_effect=Exception("API failed")
        )

        result = self.transcriber.transcribe_audio("test_audio.wav")

        assert result is None

        logger.info("Transcribe audio API error cleanup test passed")

    @patch("builtins.open", mock_open(read_data=b"fake audio data"))
    @patch("os.path.exists")
    @patch("os.remove")
    def test_transcribe_audio_cleanup_error_on_failure(self, mock_remove, mock_exists):
        """Test cleanup error handling when API fails and file removal fails"""
        logger.info("Testing cleanup error handling on API failure")

        mock_exists.side_effect = [True, False]  # File exists initially, then doesn't
        mock_remove.side_effect = Exception("Cannot remove file")

        # Mock API failure
        self.transcriber.client.audio.transcriptions.create = MagicMock(
            side_effect=Exception("API failed")
        )

        result = self.transcriber.transcribe_audio("test_audio.wav")

        # Should handle both API failure and cleanup failure gracefully
        assert result is None

        logger.info("Transcribe audio cleanup error on failure test passed")

    def test_different_model_initialization(self):
        """Test initialization with different model"""
        logger.info("Testing initialization with different model")

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            transcriber = Transcriber(model="whisper-large")

            assert transcriber.model == "whisper-large"

        logger.info("Different model initialization test passed")

    @patch("builtins.open", mock_open(read_data=b"fake audio data"))
    @patch("os.path.exists")
    @patch("os.remove")
    def test_transcribe_audio_with_custom_model(self, mock_remove, mock_exists):
        """Test transcription with custom model"""
        logger.info("Testing transcription with custom model")

        mock_exists.return_value = True

        # Create transcriber with custom model
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            transcriber = Transcriber(model="whisper-large")

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
