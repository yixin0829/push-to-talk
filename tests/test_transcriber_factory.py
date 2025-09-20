import pytest
from unittest.mock import Mock, patch

from src.transcriber_factory import TranscriberFactory


class TestTranscriberFactory:
    """Test suite for TranscriberFactory."""

    def test_get_available_models(self):
        """Test getting available models."""
        models = TranscriberFactory.get_available_models()

        assert "openai_api" in models
        assert "local_whisper" in models
        assert isinstance(models["openai_api"], list)
        assert isinstance(models["local_whisper"], list)
        assert len(models["openai_api"]) > 0
        assert len(models["local_whisper"]) > 0

    def test_is_local_model(self):
        """Test local model detection."""
        assert TranscriberFactory.is_local_model("base")
        assert TranscriberFactory.is_local_model("large-v3")
        assert not TranscriberFactory.is_local_model("whisper-1")
        assert not TranscriberFactory.is_local_model("gpt-4o-transcribe")

    def test_is_openai_model(self):
        """Test OpenAI model detection."""
        assert TranscriberFactory.is_openai_model("whisper-1")
        assert TranscriberFactory.is_openai_model("gpt-4o-transcribe")
        assert not TranscriberFactory.is_openai_model("base")
        assert not TranscriberFactory.is_openai_model("large-v3")

    def test_validate_configuration_openai_success(self):
        """Test successful OpenAI configuration validation."""
        is_valid, error = TranscriberFactory.validate_configuration(
            model_name="whisper-1", use_local_whisper=False, openai_api_key="test-key"
        )

        assert is_valid
        assert error == ""

    def test_validate_configuration_openai_missing_key(self):
        """Test OpenAI configuration validation with missing API key."""
        is_valid, error = TranscriberFactory.validate_configuration(
            model_name="whisper-1", use_local_whisper=False, openai_api_key=None
        )

        assert not is_valid
        assert "API key is required" in error

    def test_validate_configuration_openai_unknown_model(self):
        """Test OpenAI configuration validation with unknown model."""
        is_valid, error = TranscriberFactory.validate_configuration(
            model_name="unknown-model",
            use_local_whisper=False,
            openai_api_key="test-key",
        )

        assert not is_valid
        assert "Unknown OpenAI model" in error

    @patch("src.transcriber_factory.LocalWhisperTranscriber")
    def test_validate_configuration_local_success(self, mock_local_transcriber):
        """Test successful local Whisper configuration validation."""
        mock_local_transcriber.is_available.return_value = True

        is_valid, error = TranscriberFactory.validate_configuration(
            model_name="base", use_local_whisper=True, openai_api_key=None
        )

        assert is_valid
        assert error == ""

    @patch("src.transcriber_factory.LocalWhisperTranscriber")
    def test_validate_configuration_local_not_available(self, mock_local_transcriber):
        """Test local Whisper configuration validation when not available."""
        mock_local_transcriber.is_available.return_value = False

        is_valid, error = TranscriberFactory.validate_configuration(
            model_name="base", use_local_whisper=True, openai_api_key=None
        )

        assert not is_valid
        assert "pywhispercpp is not installed" in error

    @patch("src.transcriber_factory.LocalWhisperTranscriber")
    def test_validate_configuration_local_unknown_model(self, mock_local_transcriber):
        """Test local Whisper configuration validation with unknown model."""
        mock_local_transcriber.is_available.return_value = True

        is_valid, error = TranscriberFactory.validate_configuration(
            model_name="unknown-local-model",
            use_local_whisper=True,
            openai_api_key=None,
        )

        assert not is_valid
        assert "Unknown local Whisper model" in error

    @patch("src.transcriber_factory.Transcriber")
    def test_create_openai_transcriber_success(self, mock_transcriber_class):
        """Test successful OpenAI transcriber creation."""
        mock_instance = Mock()
        mock_transcriber_class.return_value = mock_instance

        transcriber = TranscriberFactory.create_transcriber(
            model_name="whisper-1", use_local_whisper=False, openai_api_key="test-key"
        )

        assert transcriber == mock_instance
        mock_transcriber_class.assert_called_once_with(
            api_key="test-key", model="whisper-1"
        )

    @patch("src.transcriber_factory.Transcriber")
    def test_create_openai_transcriber_missing_key(self, mock_transcriber_class):
        """Test OpenAI transcriber creation with missing API key."""
        with pytest.raises(ValueError, match="OpenAI API key is required"):
            TranscriberFactory.create_transcriber(
                model_name="whisper-1", use_local_whisper=False, openai_api_key=None
            )

    @patch("src.transcriber_factory.LocalWhisperTranscriber")
    def test_create_local_transcriber_success(self, mock_local_transcriber_class):
        """Test successful local Whisper transcriber creation."""
        mock_local_transcriber_class.is_available.return_value = True
        mock_instance = Mock()
        mock_local_transcriber_class.return_value = mock_instance

        transcriber = TranscriberFactory.create_transcriber(
            model_name="base",
            use_local_whisper=True,
            local_whisper_device="cuda",
            local_whisper_compute_type="float16",
        )

        assert transcriber == mock_instance
        mock_local_transcriber_class.assert_called_once_with(
            model_name="base", device="cuda", compute_type="float16"
        )

    @patch("src.transcriber_factory.LocalWhisperTranscriber")
    def test_create_local_transcriber_not_available(self, mock_local_transcriber_class):
        """Test local Whisper transcriber creation when not available."""
        mock_local_transcriber_class.is_available.return_value = False

        with pytest.raises(ValueError, match="pywhispercpp is not installed"):
            TranscriberFactory.create_transcriber(
                model_name="base", use_local_whisper=True
            )

    @patch("src.transcriber_factory.LocalWhisperTranscriber")
    def test_create_local_transcriber_initialization_failure(
        self, mock_local_transcriber_class
    ):
        """Test local Whisper transcriber creation with initialization failure."""
        mock_local_transcriber_class.is_available.return_value = True
        mock_local_transcriber_class.side_effect = RuntimeError("Model loading failed")

        with pytest.raises(
            ValueError, match="Failed to initialize local Whisper model"
        ):
            TranscriberFactory.create_transcriber(
                model_name="base", use_local_whisper=True
            )

    @patch("src.transcriber_factory.Transcriber")
    def test_create_openai_transcriber_initialization_failure(
        self, mock_transcriber_class
    ):
        """Test OpenAI transcriber creation with initialization failure."""
        mock_transcriber_class.side_effect = RuntimeError("API connection failed")

        with pytest.raises(ValueError, match="Failed to initialize OpenAI transcriber"):
            TranscriberFactory.create_transcriber(
                model_name="whisper-1",
                use_local_whisper=False,
                openai_api_key="test-key",
            )

    def test_create_transcriber_with_default_local_params(self):
        """Test transcriber creation with default local whisper parameters."""
        with patch("src.transcriber_factory.LocalWhisperTranscriber") as mock_local:
            mock_local.is_available.return_value = True
            mock_instance = Mock()
            mock_local.return_value = mock_instance

            transcriber = TranscriberFactory.create_transcriber(
                model_name="base", use_local_whisper=True
            )

            assert transcriber == mock_instance
            mock_local.assert_called_once_with(
                model_name="base", device="auto", compute_type="auto"
            )
