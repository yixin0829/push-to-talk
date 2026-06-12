import pytest
import os
from loguru import logger
from unittest.mock import MagicMock

import httpx

from src.transcription_sixtydb import SixtyDBTranscriber
from src.exceptions import ConfigurationError, TranscriptionError, APIError


def _make_response(json_data, status_code=200):
    """Build a mock httpx response with the given JSON payload."""
    mock_response = MagicMock()
    mock_response.json.return_value = json_data
    mock_response.raise_for_status.return_value = None
    mock_response.status_code = status_code
    return mock_response


class TestSixtyDBTranscriber:
    @pytest.fixture(autouse=True)
    def setup(self, mocker):
        """Setup for each test method"""
        logger.info("Setting up SixtyDBTranscriber test")

        # Use a mock API key for testing
        mocker.patch.dict(os.environ, {"SIXTYDB_API_KEY": "test-api-key"})
        self.transcriber = SixtyDBTranscriber()

    def test_initialization_with_env_var(self, mocker):
        """Test SixtyDBTranscriber initialization with environment variable"""
        logger.info("Testing SixtyDBTranscriber initialization with env var")

        mocker.patch.dict(os.environ, {"SIXTYDB_API_KEY": "env-api-key"})
        transcriber = SixtyDBTranscriber()

        assert transcriber.api_key == "env-api-key"
        assert transcriber.model == "60db-stt"

        logger.info("SixtyDBTranscriber initialization with env var test passed")

    def test_initialization_with_explicit_key(self):
        """Test SixtyDBTranscriber initialization with explicit API key"""
        logger.info("Testing SixtyDBTranscriber initialization with explicit key")

        transcriber = SixtyDBTranscriber(api_key="explicit-api-key")

        assert transcriber.api_key == "explicit-api-key"

        logger.info("SixtyDBTranscriber initialization with explicit key test passed")

    def test_initialization_no_api_key(self, mocker):
        """Test SixtyDBTranscriber initialization without API key"""
        logger.info("Testing SixtyDBTranscriber initialization without API key")

        mocker.patch.dict(os.environ, {}, clear=True)
        with pytest.raises(ConfigurationError) as exc_info:
            SixtyDBTranscriber()

        assert "60dB API key is required" in str(exc_info.value)

        logger.info("SixtyDBTranscriber initialization no API key test passed")

    def test_transcribe_audio_success(self, mocker):
        """Test successful audio transcription"""
        logger.info("Testing successful audio transcription")

        mocker.patch("builtins.open", mocker.mock_open(read_data=b"fake audio data"))
        mocker.patch("os.path.exists", return_value=True)

        mock_post = mocker.patch(
            "src.transcription_sixtydb.httpx.post",
            return_value=_make_response({"text": "This is the transcribed text."}),
        )

        result = self.transcriber.transcribe_audio("test_audio.wav")

        assert result == "This is the transcribed text."

        # Verify the API was called once with the auth header
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["headers"]["Authorization"] == "Bearer test-api-key"
        assert "file" in call_kwargs["files"]

        logger.info("Transcribe audio success test passed")

    def test_transcribe_audio_with_language(self, mocker):
        """Test audio transcription with language specified"""
        logger.info("Testing audio transcription with language")

        mocker.patch("builtins.open", mocker.mock_open(read_data=b"fake audio data"))
        mocker.patch("os.path.exists", return_value=True)

        mock_post = mocker.patch(
            "src.transcription_sixtydb.httpx.post",
            return_value=_make_response({"text": "This is transcribed French text."}),
        )

        result = self.transcriber.transcribe_audio("test_audio.wav", language="fr")

        assert result == "This is transcribed French text."

        # Verify language parameter was passed in form data
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["data"]["language"] == "fr"

        logger.info("Transcribe audio with language test passed")

    def test_transcribe_audio_file_not_found(self, mocker):
        """Test transcription when audio file doesn't exist"""
        logger.info("Testing transcription with missing file")

        mocker.patch("os.path.exists", return_value=False)

        result = self.transcriber.transcribe_audio("nonexistent.wav")

        assert result is None

        logger.info("Transcribe audio file not found test passed")

    def test_transcribe_audio_generic_failure(self, mocker):
        """Test generic transcription failure raises TranscriptionError"""
        logger.info("Testing transcription generic failure")

        mocker.patch("builtins.open", mocker.mock_open(read_data=b"fake audio data"))
        mocker.patch("os.path.exists", return_value=True)

        mocker.patch(
            "src.transcription_sixtydb.httpx.post",
            side_effect=Exception("connection failed"),
        )

        with pytest.raises(TranscriptionError, match="Failed to transcribe audio"):
            self.transcriber.transcribe_audio("test_audio.wav")

        logger.info("Transcribe audio generic failure test passed")

    def test_transcribe_audio_http_error(self, mocker):
        """Test that HTTP status errors raise APIError with status code"""
        logger.info("Testing 60dB API error handling")

        mocker.patch("builtins.open", mocker.mock_open(read_data=b"fake audio data"))
        mocker.patch("os.path.exists", return_value=True)

        request = httpx.Request("POST", "https://api.60db.ai/stt")
        response = httpx.Response(429, request=request)
        http_error = httpx.HTTPStatusError(
            "rate limit", request=request, response=response
        )

        mock_response = _make_response({})
        mock_response.raise_for_status.side_effect = http_error
        mocker.patch(
            "src.transcription_sixtydb.httpx.post", return_value=mock_response
        )

        with pytest.raises(APIError, match="60dB transcription API failed") as exc_info:
            self.transcriber.transcribe_audio("test_audio.wav")

        assert exc_info.value.status_code == 429
        assert exc_info.value.provider == "60dB"

        logger.info("60dB API error test passed")

    def test_transcribe_audio_empty_response(self, mocker):
        """Test transcription with empty transcript"""
        logger.info("Testing transcription with empty response")

        mocker.patch("builtins.open", mocker.mock_open(read_data=b"fake audio data"))
        mocker.patch("os.path.exists", return_value=True)

        mocker.patch(
            "src.transcription_sixtydb.httpx.post",
            return_value=_make_response({"text": ""}),
        )

        result = self.transcriber.transcribe_audio("test_audio.wav")

        assert result is None

        logger.info("Transcribe audio empty response test passed")

    def test_transcribe_audio_whitespace_response(self, mocker):
        """Test transcription with whitespace-only transcript"""
        logger.info("Testing transcription with whitespace response")

        mocker.patch("builtins.open", mocker.mock_open(read_data=b"fake audio data"))
        mocker.patch("os.path.exists", return_value=True)

        mocker.patch(
            "src.transcription_sixtydb.httpx.post",
            return_value=_make_response({"text": "   \n  \t  "}),
        )

        result = self.transcriber.transcribe_audio("test_audio.wav")

        assert result is None

        logger.info("Transcribe audio whitespace response test passed")

    def test_transcribe_audio_missing_text_field(self, mocker):
        """Test transcription when response has no 'text' field"""
        logger.info("Testing transcription with missing text field")

        mocker.patch("builtins.open", mocker.mock_open(read_data=b"fake audio data"))
        mocker.patch("os.path.exists", return_value=True)

        mocker.patch(
            "src.transcription_sixtydb.httpx.post",
            return_value=_make_response({"language": "en"}),
        )

        result = self.transcriber.transcribe_audio("test_audio.wav")

        assert result is None

        logger.info("Transcribe audio missing text field test passed")

    def test_transcribe_audio_with_glossary(self, mocker):
        """Test transcription maps glossary to keyword boosting"""
        logger.info("Testing transcription with glossary/keyword boosting")

        mocker.patch("builtins.open", mocker.mock_open(read_data=b"fake audio data"))
        mocker.patch("os.path.exists", return_value=True)

        glossary = ["Deepgram", "Nova-3", "API"]
        self.transcriber.set_glossary(glossary)

        mock_post = mocker.patch(
            "src.transcription_sixtydb.httpx.post",
            return_value=_make_response({"text": "Deepgram Nova-3 API"}),
        )

        result = self.transcriber.transcribe_audio("test_audio.wav")

        assert result == "Deepgram Nova-3 API"

        # Verify keywords were passed as weighted CSV
        call_kwargs = mock_post.call_args[1]
        assert "keywords" in call_kwargs["data"]
        keywords = call_kwargs["data"]["keywords"]
        assert "Deepgram:5" in keywords
        assert "Nova-3:5" in keywords
        assert keywords.count(",") == 2  # three terms -> two separators

        logger.info("Transcribe audio with glossary test passed")

    def test_transcribe_audio_with_large_glossary(self, mocker):
        """Test transcription with large glossary that exceeds the char budget"""
        logger.info("Testing transcription with large glossary")

        mocker.patch("builtins.open", mocker.mock_open(read_data=b"fake audio data"))
        mocker.patch("os.path.exists", return_value=True)

        large_glossary = [f"term_{i}_" + "x" * 100 for i in range(50)]
        self.transcriber.set_glossary(large_glossary)

        mock_post = mocker.patch(
            "src.transcription_sixtydb.httpx.post",
            return_value=_make_response({"text": "limited keywords"}),
        )

        result = self.transcriber.transcribe_audio("test_audio.wav")

        assert result == "limited keywords"

        # Verify the keywords string stayed within the char budget
        call_kwargs = mock_post.call_args[1]
        keywords = call_kwargs["data"]["keywords"]
        assert len(keywords) <= self.transcriber.MAX_KEYWORD_CHARS
        # Not all terms fit
        assert keywords.count(",") + 1 < len(large_glossary)

        logger.info("Transcribe audio with large glossary test passed")

    def test_prepare_keywords_empty(self):
        """Test keyword preparation with an empty glossary"""
        logger.info("Testing keyword preparation with empty glossary")

        assert self.transcriber._prepare_keywords([]) == ""

        logger.info("Prepare keywords empty test passed")
