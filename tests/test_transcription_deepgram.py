import pytest
import os
from loguru import logger
from unittest.mock import MagicMock

from src.transcription_deepgram import DeepgramTranscriber
from src.exceptions import ConfigurationError


class TestDeepgramTranscriber:
    @pytest.fixture(autouse=True)
    def setup(self, mocker):
        """Setup for each test method"""
        logger.info("Setting up DeepgramTranscriber test")

        # Use a mock API key for testing
        mocker.patch.dict(os.environ, {"DEEPGRAM_API_KEY": "test-api-key"})
        self.transcriber = DeepgramTranscriber()

    def test_initialization_with_env_var(self, mocker):
        """Test DeepgramTranscriber initialization with environment variable"""
        logger.info("Testing DeepgramTranscriber initialization with env var")

        mocker.patch.dict(os.environ, {"DEEPGRAM_API_KEY": "env-api-key"})
        transcriber = DeepgramTranscriber()

        assert transcriber.api_key == "env-api-key"
        assert transcriber.model == "nova-3"
        assert transcriber.client is not None

        logger.info("DeepgramTranscriber initialization with env var test passed")

    def test_initialization_with_explicit_key(self):
        """Test DeepgramTranscriber initialization with explicit API key"""
        logger.info("Testing DeepgramTranscriber initialization with explicit key")

        transcriber = DeepgramTranscriber(api_key="explicit-api-key", model="base")

        assert transcriber.api_key == "explicit-api-key"
        assert transcriber.model == "base"
        assert transcriber.client is not None

        logger.info("DeepgramTranscriber initialization with explicit key test passed")

    def test_initialization_no_api_key(self, mocker):
        """Test DeepgramTranscriber initialization without API key"""
        logger.info("Testing DeepgramTranscriber initialization without API key")

        mocker.patch.dict(os.environ, {}, clear=True)
        with pytest.raises(ConfigurationError) as exc_info:
            DeepgramTranscriber()

        assert "Deepgram API key is required" in str(exc_info.value)

        logger.info("DeepgramTranscriber initialization no API key test passed")

    def test_transcribe_audio_success(self, mocker):
        """Test successful audio transcription"""
        logger.info("Testing successful audio transcription")

        mocker.patch("builtins.open", mocker.mock_open(read_data=b"fake audio data"))
        mocker.patch("os.path.exists", return_value=True)

        # Mock the Deepgram client response
        mock_response = MagicMock()
        mock_response.results.channels = [MagicMock()]
        mock_response.results.channels[0].alternatives = [MagicMock()]
        mock_response.results.channels[0].alternatives[
            0
        ].transcript = "This is the transcribed text."

        self.transcriber.client.listen.v1.media.transcribe_file = MagicMock(
            return_value=mock_response
        )

        result = self.transcriber.transcribe_audio("test_audio.wav")

        assert result == "This is the transcribed text."

        # Verify the API was called correctly
        self.transcriber.client.listen.v1.media.transcribe_file.assert_called_once()
        call_kwargs = self.transcriber.client.listen.v1.media.transcribe_file.call_args[
            1
        ]
        assert call_kwargs["model"] == "nova-3"
        assert call_kwargs["smart_format"] is True

        logger.info("Transcribe audio success test passed")

    def test_transcribe_audio_with_language(self, mocker):
        """Test audio transcription with language specified"""
        logger.info("Testing audio transcription with language")

        mocker.patch("builtins.open", mocker.mock_open(read_data=b"fake audio data"))
        mocker.patch("os.path.exists", return_value=True)

        # Mock the Deepgram response
        mock_response = MagicMock()
        mock_response.results.channels = [MagicMock()]
        mock_response.results.channels[0].alternatives = [MagicMock()]
        mock_response.results.channels[0].alternatives[
            0
        ].transcript = "This is transcribed French text."

        self.transcriber.client.listen.v1.media.transcribe_file = MagicMock(
            return_value=mock_response
        )

        result = self.transcriber.transcribe_audio("test_audio.wav", language="fr")

        assert result == "This is transcribed French text."

        # Verify language parameter was passed
        call_kwargs = self.transcriber.client.listen.v1.media.transcribe_file.call_args[
            1
        ]
        assert call_kwargs["language"] == "fr"

        logger.info("Transcribe audio with language test passed")

    def test_transcribe_audio_file_not_found(self, mocker):
        """Test transcription when audio file doesn't exist"""
        logger.info("Testing transcription with missing file")

        mocker.patch("os.path.exists", return_value=False)

        result = self.transcriber.transcribe_audio("nonexistent.wav")

        assert result is None

        logger.info("Transcribe audio file not found test passed")

    def test_transcribe_audio_api_failure(self, mocker):
        """Test transcription API failure"""
        logger.info("Testing transcription API failure")

        mocker.patch("builtins.open", mocker.mock_open(read_data=b"fake audio data"))
        mocker.patch("os.path.exists", return_value=True)

        # Mock API failure
        self.transcriber.client.listen.v1.media.transcribe_file = MagicMock(
            side_effect=Exception("API request failed")
        )

        result = self.transcriber.transcribe_audio("test_audio.wav")

        assert result is None

        logger.info("Transcribe audio API failure test passed")

    def test_transcribe_audio_empty_response(self, mocker):
        """Test transcription with empty response"""
        logger.info("Testing transcription with empty response")

        mocker.patch("builtins.open", mocker.mock_open(read_data=b"fake audio data"))
        mocker.patch("os.path.exists", return_value=True)

        # Mock empty transcript
        mock_response = MagicMock()
        mock_response.results.channels = [MagicMock()]
        mock_response.results.channels[0].alternatives = [MagicMock()]
        mock_response.results.channels[0].alternatives[0].transcript = ""

        self.transcriber.client.listen.v1.media.transcribe_file = MagicMock(
            return_value=mock_response
        )

        result = self.transcriber.transcribe_audio("test_audio.wav")

        assert result is None

        logger.info("Transcribe audio empty response test passed")

    def test_transcribe_audio_whitespace_response(self, mocker):
        """Test transcription with whitespace-only response"""
        logger.info("Testing transcription with whitespace response")

        mocker.patch("builtins.open", mocker.mock_open(read_data=b"fake audio data"))
        mocker.patch("os.path.exists", return_value=True)

        # Mock whitespace response
        mock_response = MagicMock()
        mock_response.results.channels = [MagicMock()]
        mock_response.results.channels[0].alternatives = [MagicMock()]
        mock_response.results.channels[0].alternatives[0].transcript = "   \n  \t  "

        self.transcriber.client.listen.v1.media.transcribe_file = MagicMock(
            return_value=mock_response
        )

        result = self.transcriber.transcribe_audio("test_audio.wav")

        assert result is None

        logger.info("Transcribe audio whitespace response test passed")

    def test_transcribe_audio_no_alternatives(self, mocker):
        """Test transcription with no alternatives in response"""
        logger.info("Testing transcription with no alternatives")

        mocker.patch("builtins.open", mocker.mock_open(read_data=b"fake audio data"))
        mocker.patch("os.path.exists", return_value=True)

        # Mock response without alternatives
        mock_response = MagicMock()
        mock_response.results.channels = [MagicMock()]
        mock_response.results.channels[0].alternatives = []

        self.transcriber.client.listen.v1.media.transcribe_file = MagicMock(
            return_value=mock_response
        )

        result = self.transcriber.transcribe_audio("test_audio.wav")

        assert result is None

        logger.info("Transcribe audio no alternatives test passed")

    def test_transcribe_audio_no_channels(self, mocker):
        """Test transcription with no channels in response"""
        logger.info("Testing transcription with no channels")

        mocker.patch("builtins.open", mocker.mock_open(read_data=b"fake audio data"))
        mocker.patch("os.path.exists", return_value=True)

        # Mock response without channels
        mock_response = MagicMock()
        mock_response.results.channels = []

        self.transcriber.client.listen.v1.media.transcribe_file = MagicMock(
            return_value=mock_response
        )

        result = self.transcriber.transcribe_audio("test_audio.wav")

        assert result is None

        logger.info("Transcribe audio no channels test passed")

    def test_transcribe_audio_timing(self, mocker):
        """Test transcription timing measurement"""
        logger.info("Testing transcription timing measurement")

        mocker.patch("builtins.open", mocker.mock_open(read_data=b"fake audio data"))
        mocker.patch("os.path.exists", return_value=True)

        # Mock time progression
        mock_time = mocker.patch("time.time")
        mock_time.side_effect = [1000.0, 1002.5, 1002.6, 1002.7]

        # Mock response
        mock_response = MagicMock()
        mock_response.results.channels = [MagicMock()]
        mock_response.results.channels[0].alternatives = [MagicMock()]
        mock_response.results.channels[0].alternatives[
            0
        ].transcript = "Timed transcription"

        self.transcriber.client.listen.v1.media.transcribe_file = MagicMock(
            return_value=mock_response
        )

        result = self.transcriber.transcribe_audio("test_audio.wav")

        assert result == "Timed transcription"

        # Verify time.time() was called at least twice (start and end)
        assert mock_time.call_count >= 2

        logger.info("Transcribe audio timing test passed")

    def test_different_model_initialization(self, mocker):
        """Test initialization with different model"""
        logger.info("Testing initialization with different model")

        mocker.patch.dict(os.environ, {"DEEPGRAM_API_KEY": "test-key"})
        transcriber = DeepgramTranscriber(model="whisper-cloud")

        assert transcriber.model == "whisper-cloud"

        logger.info("Different model initialization test passed")

    def test_transcribe_audio_with_custom_model(self, mocker):
        """Test transcription with custom model"""
        logger.info("Testing transcription with custom model")

        mocker.patch("builtins.open", mocker.mock_open(read_data=b"fake audio data"))
        mocker.patch("os.path.exists", return_value=True)

        # Create transcriber with custom model
        mocker.patch.dict(os.environ, {"DEEPGRAM_API_KEY": "test-key"})
        transcriber = DeepgramTranscriber(model="base")

        # Mock response
        mock_response = MagicMock()
        mock_response.results.channels = [MagicMock()]
        mock_response.results.channels[0].alternatives = [MagicMock()]
        mock_response.results.channels[0].alternatives[
            0
        ].transcript = "Custom model transcription"

        transcriber.client.listen.v1.media.transcribe_file = MagicMock(
            return_value=mock_response
        )

        result = transcriber.transcribe_audio("test_audio.wav")

        assert result == "Custom model transcription"

        # Verify custom model was used
        call_kwargs = transcriber.client.listen.v1.media.transcribe_file.call_args[1]
        assert call_kwargs["model"] == "base"

        logger.info("Transcribe audio with custom model test passed")

    def test_transcribe_audio_with_glossary(self, mocker):
        """Test transcription with glossary/keyterm prompting"""
        logger.info("Testing transcription with glossary/keyterm prompting")

        mocker.patch("builtins.open", mocker.mock_open(read_data=b"fake audio data"))
        mocker.patch("os.path.exists", return_value=True)

        # Set glossary terms
        glossary = ["Deepgram", "Nova-3", "API", "transcription", "keyterm"]
        self.transcriber.set_glossary(glossary)

        # Mock response
        mock_response = MagicMock()
        mock_response.results.channels = [MagicMock()]
        mock_response.results.channels[0].alternatives = [MagicMock()]
        mock_response.results.channels[0].alternatives[
            0
        ].transcript = "Deepgram Nova-3 API transcription with keyterm"

        self.transcriber.client.listen.v1.media.transcribe_file = MagicMock(
            return_value=mock_response
        )

        result = self.transcriber.transcribe_audio("test_audio.wav")

        assert result == "Deepgram Nova-3 API transcription with keyterm"

        # Verify keyterms were passed to API
        call_kwargs = self.transcriber.client.listen.v1.media.transcribe_file.call_args[
            1
        ]
        assert "keyterm" in call_kwargs
        assert call_kwargs["keyterm"] == glossary

        logger.info("Transcribe audio with glossary test passed")

    def test_transcribe_audio_with_large_glossary(self, mocker):
        """Test transcription with large glossary that exceeds token limit"""
        logger.info("Testing transcription with large glossary")

        mocker.patch("builtins.open", mocker.mock_open(read_data=b"fake audio data"))
        mocker.patch("os.path.exists", return_value=True)

        # Create a large glossary that would exceed token limit
        large_glossary = [
            f"term_{i}_" + "x" * 100 for i in range(50)
        ]  # 50 terms with ~100 chars each
        self.transcriber.set_glossary(large_glossary)

        # Mock response
        mock_response = MagicMock()
        mock_response.results.channels = [MagicMock()]
        mock_response.results.channels[0].alternatives = [MagicMock()]
        mock_response.results.channels[0].alternatives[
            0
        ].transcript = "Transcription with limited keyterms"

        self.transcriber.client.listen.v1.media.transcribe_file = MagicMock(
            return_value=mock_response
        )

        result = self.transcriber.transcribe_audio("test_audio.wav")

        assert result == "Transcription with limited keyterms"

        # Verify keyterms were limited
        call_kwargs = self.transcriber.client.listen.v1.media.transcribe_file.call_args[
            1
        ]
        assert "keyterm" in call_kwargs
        # Should have limited the number of keyterms
        assert len(call_kwargs["keyterm"]) < len(large_glossary)

        logger.info("Transcribe audio with large glossary test passed")

    def test_transcribe_audio_with_unsupported_model(self, mocker):
        """Test that glossary is not used with unsupported models"""
        logger.info("Testing glossary with unsupported model")

        mocker.patch("builtins.open", mocker.mock_open(read_data=b"fake audio data"))
        mocker.patch("os.path.exists", return_value=True)

        # Create transcriber with unsupported model for keyterms
        mocker.patch.dict(os.environ, {"DEEPGRAM_API_KEY": "test-key"})
        transcriber = DeepgramTranscriber(model="base")

        # Set glossary
        glossary = ["test", "terms"]
        transcriber.set_glossary(glossary)

        # Mock response
        mock_response = MagicMock()
        mock_response.results.channels = [MagicMock()]
        mock_response.results.channels[0].alternatives = [MagicMock()]
        mock_response.results.channels[0].alternatives[
            0
        ].transcript = "Transcription without keyterms"

        transcriber.client.listen.v1.media.transcribe_file = MagicMock(
            return_value=mock_response
        )

        result = transcriber.transcribe_audio("test_audio.wav")

        assert result == "Transcription without keyterms"

        # Verify keyterms were NOT passed for unsupported model
        call_kwargs = transcriber.client.listen.v1.media.transcribe_file.call_args[1]
        assert "keyterm" not in call_kwargs

        logger.info("Glossary with unsupported model test passed")
