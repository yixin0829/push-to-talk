import pytest
import os
from loguru import logger
from unittest.mock import MagicMock

from src.text_refiner_openai import TextRefinerOpenAI


class TestTextRefinerOpenAI:
    @pytest.fixture(autouse=True)
    def setup(self, mocker):
        """Setup for each test method"""
        logger.info("Setting up TextRefinerOpenAI test")

        # Use a mock API key for testing
        mocker.patch.dict(os.environ, {"OPENAI_API_KEY": "test-api-key"})
        self.refiner = TextRefinerOpenAI()

    def test_initialization_with_env_var(self, mocker):
        """Test TextRefinerOpenAI initialization with environment variable"""
        logger.info("Testing TextRefinerOpenAI initialization with env var")

        mocker.patch.dict(os.environ, {"OPENAI_API_KEY": "env-api-key"})
        refiner = TextRefinerOpenAI()

        assert refiner.api_key == "env-api-key"
        assert refiner.model == "gpt-4.1-nano"
        assert refiner.client is not None
        assert refiner.custom_refinement_prompt is None

        logger.info("TextRefinerOpenAI initialization with env var test passed")

    def test_initialization_with_explicit_key(self):
        """Test TextRefinerOpenAI initialization with explicit API key"""
        logger.info("Testing TextRefinerOpenAI initialization with explicit key")

        refiner = TextRefinerOpenAI(api_key="explicit-api-key", model="gpt-4")

        assert refiner.api_key == "explicit-api-key"
        assert refiner.model == "gpt-4"
        assert refiner.client is not None

        logger.info("TextRefinerOpenAI initialization with explicit key test passed")

    def test_initialization_no_api_key(self, mocker):
        """Test TextRefinerOpenAI initialization without API key"""
        logger.info("Testing TextRefinerOpenAI initialization without API key")

        mocker.patch.dict(os.environ, {}, clear=True)
        with pytest.raises(ValueError) as exc_info:
            TextRefinerOpenAI()

        assert "OpenAI API key is required" in str(exc_info.value)

        logger.info("TextRefinerOpenAI initialization no API key test passed")

    def test_refine_text_success(self):
        """Test successful text refinement"""
        logger.info("Testing successful text refinement")

        # Mock the OpenAI client response
        mock_response = MagicMock()
        mock_response.output_text = "This is the refined text with proper punctuation."
        self.refiner.client.responses.create = MagicMock(return_value=mock_response)

        raw_text = "this is some rough transcribed text without punctuation"
        result = self.refiner.refine_text(raw_text)

        assert result == "This is the refined text with proper punctuation."

        # Verify the API was called correctly
        self.refiner.client.responses.create.assert_called_once()
        call_args = self.refiner.client.responses.create.call_args
        assert call_args[1]["model"] == "gpt-4.1-nano"
        # Should use default prompt since no custom prompt is set
        expected_prompt = self.refiner._get_default_developer_prompt()
        assert call_args[1]["instructions"] == expected_prompt
        assert raw_text in call_args[1]["input"]

        logger.info("Refine text success test passed")

    def test_refine_text_with_custom_prompt(self, mocker):
        """Test text refinement with custom prompt"""
        logger.info("Testing text refinement with custom prompt")

        mock_response = MagicMock()
        mock_response.output_text = "Custom refined text."

        # Set custom prompt first
        custom_prompt = "Custom refinement instructions"
        self.refiner.set_custom_prompt(custom_prompt)

        mock_create = mocker.patch.object(
            self.refiner.client.responses, "create", return_value=mock_response
        )
        raw_text = (
            "some text to refine with custom prompt that is long enough"  # >20 chars
        )
        result = self.refiner.refine_text(raw_text)

        assert result == "Custom refined text."

        # Verify custom prompt was used in the API call
        mock_create.assert_called_once()
        call_args = mock_create.call_args
        assert call_args[1]["instructions"] == custom_prompt

        logger.info("Refine text with custom prompt test passed")

    def test_refine_text_empty_input(self):
        """Test refinement with empty input"""
        logger.info("Testing refinement with empty input")

        result = self.refiner.refine_text("")
        assert result is None

        result = self.refiner.refine_text("   ")
        assert result is None

        result = self.refiner.refine_text(None)
        assert result is None

        logger.info("Refine text empty input test passed")

    def test_refine_text_too_short(self, mocker):
        """Test refinement with text too short"""
        logger.info("Testing refinement with text too short")

        short_text = "Hi there"  # Less than 20 characters
        result = self.refiner.refine_text(short_text)

        # Should return original text without API call
        assert result == short_text

        # Verify API was not called
        mock_create = mocker.patch.object(self.refiner.client.responses, "create")
        self.refiner.refine_text(short_text)
        mock_create.assert_not_called()

        logger.info("Refine text too short test passed")

    def test_refine_text_api_failure(self):
        """Test text refinement API failure"""
        logger.info("Testing text refinement API failure")

        # Mock API failure
        self.refiner.client.responses.create = MagicMock(
            side_effect=Exception("API request failed")
        )

        raw_text = "this is some text that should cause an api failure"
        result = self.refiner.refine_text(raw_text)

        # Should return original text on API failure
        assert result == raw_text.strip()

        logger.info("Refine text API failure test passed")

    def test_refine_text_empty_api_response(self):
        """Test refinement with empty API response"""
        logger.info("Testing refinement with empty API response")

        mock_response = MagicMock()
        mock_response.output_text = ""
        self.refiner.client.responses.create = MagicMock(return_value=mock_response)

        raw_text = "some text to refine but api returns empty"
        result = self.refiner.refine_text(raw_text)

        # Should return original text when API returns empty
        assert result == raw_text.strip()

        logger.info("Refine text empty API response test passed")

    def test_refine_text_none_api_response(self):
        """Test refinement with None API response"""
        logger.info("Testing refinement with None API response")

        mock_response = MagicMock()
        mock_response.output_text = None
        self.refiner.client.responses.create = MagicMock(return_value=mock_response)

        raw_text = "some text to refine but api returns none"
        result = self.refiner.refine_text(raw_text)

        # Should return original text when API returns None
        assert result == raw_text.strip()

        logger.info("Refine text None API response test passed")

    def test_refine_text_gpt5_model_settings(self, mocker):
        """Test refinement with GPT-5 model settings"""
        logger.info("Testing refinement with GPT-5 model settings")

        # Create refiner with GPT-5 model
        mocker.patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
        refiner = TextRefinerOpenAI(model="gpt-5-preview")

        mock_response = MagicMock()
        mock_response.output_text = "GPT-5 refined text"
        refiner.client.responses.create = MagicMock(return_value=mock_response)

        raw_text = "text to refine with gpt5 reasoning settings"
        result = refiner.refine_text(raw_text)

        assert result == "GPT-5 refined text"

        # Verify reasoning parameter was added for GPT-5
        call_args = refiner.client.responses.create.call_args
        assert "reasoning" in call_args[1]
        assert call_args[1]["reasoning"]["effort"] == "minimal"

        logger.info("Refine text GPT-5 model settings test passed")

    def test_refine_text_non_gpt5_model_settings(self):
        """Test refinement with non-GPT-5 model settings"""
        logger.info("Testing refinement with non-GPT-5 model settings")

        mock_response = MagicMock()
        mock_response.output_text = "Non-GPT-5 refined text"
        self.refiner.client.responses.create = MagicMock(return_value=mock_response)

        raw_text = "text to refine with standard settings"
        result = self.refiner.refine_text(raw_text)

        assert result == "Non-GPT-5 refined text"

        # Verify reasoning parameter was NOT added for non-GPT-5
        call_args = self.refiner.client.responses.create.call_args
        assert "reasoning" not in call_args[1]
        assert call_args[1]["temperature"] == 0.3

        logger.info("Refine text non-GPT-5 model settings test passed")

    def test_refine_text_timing(self, mocker):
        """Test refinement timing measurement"""
        logger.info("Testing refinement timing measurement")

        # Mock time progression - need more calls for logging
        mock_time = mocker.patch("time.time")
        mock_time.side_effect = [1000.0, 1001.5, 1001.6, 1001.7, 1001.8, 1001.9]

        mock_response = MagicMock()
        mock_response.output_text = "Timed refined text"
        self.refiner.client.responses.create = MagicMock(return_value=mock_response)

        raw_text = "text to refine with timing measurement"
        result = self.refiner.refine_text(raw_text)

        assert result == "Timed refined text"

        # Verify time.time() was called at least twice (start and end)
        assert mock_time.call_count >= 2

        logger.info("Refine text timing test passed")

    def test_set_custom_prompt(self):
        """Test setting custom prompt"""
        logger.info("Testing setting custom prompt")

        new_prompt = "This is a custom refinement prompt for testing."
        self.refiner.set_custom_prompt(new_prompt)

        assert self.refiner.custom_refinement_prompt == new_prompt

        logger.info("Set custom prompt test passed")

    def test_get_current_prompt(self):
        """Test getting current prompt"""
        logger.info("Testing getting current prompt")

        # Test when no custom prompt is set
        current_prompt = self.refiner.get_current_prompt()
        assert current_prompt is None

        # Test when custom prompt is set
        custom_prompt = "Custom test prompt with Role and Objective"
        self.refiner.set_custom_prompt(custom_prompt)
        current_prompt = self.refiner.get_current_prompt()

        assert current_prompt == custom_prompt
        assert "Role and Objective" in current_prompt

        logger.info("Get current prompt test passed")

    def test_custom_prompt_usage(self):
        """Test that custom prompt is actually used"""
        logger.info("Testing custom prompt usage")

        # Set a custom prompt
        custom_prompt = "Custom prompt for testing"
        self.refiner.set_custom_prompt(custom_prompt)

        mock_response = MagicMock()
        mock_response.output_text = "Text refined with custom prompt"
        self.refiner.client.responses.create = MagicMock(return_value=mock_response)

        raw_text = "text to refine with custom prompt"
        result = self.refiner.refine_text(raw_text)

        assert result == "Text refined with custom prompt"

        # Verify custom prompt was used in the API call
        call_args = self.refiner.client.responses.create.call_args
        assert call_args[1]["instructions"] == custom_prompt

        logger.info("Custom prompt usage test passed")

    def test_default_prompt_content(self):
        """Test that default prompt contains expected content"""
        logger.info("Testing default prompt content")

        # Get the default developer prompt directly since get_current_prompt() returns None when no custom prompt is set
        default_prompt = self.refiner._get_default_developer_prompt()

        # Check for key elements of the default prompt
        assert "Role and Objective" in default_prompt
        assert "Instructions" in default_prompt
        assert "Output Format" in default_prompt
        assert "Refine transcribed speech-to-text outputs" in default_prompt
        assert "Preserve the original meaning and intent" in default_prompt
        assert "formatting compliance" in default_prompt

        logger.info("Default prompt content test passed")

    def test_refine_text_whitespace_handling(self):
        """Test refinement with various whitespace scenarios"""
        logger.info("Testing refinement whitespace handling")

        mock_response = MagicMock()
        mock_response.output_text = "Refined text without extra whitespace"
        self.refiner.client.responses.create = MagicMock(return_value=mock_response)

        # Test with leading/trailing whitespace
        raw_text = "   text with whitespace   "
        result = self.refiner.refine_text(raw_text)

        assert result == "Refined text without extra whitespace"

        # Verify original text was stripped before API call
        call_args = self.refiner.client.responses.create.call_args
        assert "text with whitespace" in call_args[1]["input"]

        logger.info("Refine text whitespace handling test passed")

    def test_refine_text_length_boundary(self):
        """Test refinement at the length boundary (20 characters)"""
        logger.info("Testing refinement at length boundary")

        # Exactly 20 characters - should be refined
        text_20_chars = "This is twenty chars"  # Exactly 20
        assert len(text_20_chars) == 20

        mock_response = MagicMock()
        mock_response.output_text = "Refined twenty character text"
        self.refiner.client.responses.create = MagicMock(return_value=mock_response)

        result = self.refiner.refine_text(text_20_chars)
        assert result == "Refined twenty character text"

        # 19 characters - should not be refined
        text_19_chars = "This is nineteen ch"  # 19 characters
        assert len(text_19_chars) == 19

        result = self.refiner.refine_text(text_19_chars)
        assert result == text_19_chars  # Should return original

        logger.info("Refine text length boundary test passed")
