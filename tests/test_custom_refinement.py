import pytest
from src.push_to_talk import PushToTalkConfig, PushToTalkApp


class TestCustomRefinement:
    def test_config_custom_provider_fields(self):
        """Test that PushToTalkConfig supports custom provider fields."""
        config = PushToTalkConfig(
            refinement_provider="custom",
            custom_api_key="test-custom-key",
            custom_endpoint="http://localhost:11434/v1",
        )
        assert config.refinement_provider == "custom"
        assert config.custom_api_key == "test-custom-key"
        assert config.custom_endpoint == "http://localhost:11434/v1"

    def test_app_initialization_with_custom_provider(self, mocker):
        """Test that PushToTalkApp correctly initializes refiner with custom settings."""
        # Mock TextRefinerFactory to verify calls
        mock_factory = mocker.patch("src.push_to_talk.TextRefinerFactory")

        # Mock TextInserter (pynput.keyboard fails in headless environment)
        mocker.patch("src.push_to_talk.TextInserter")
        # Also mock HotkeyService as it might also use pynput
        mocker.patch("src.push_to_talk.HotkeyService")
        # Mock AudioRecorder to avoid audio device issues
        mocker.patch("src.push_to_talk.AudioRecorder")

        config = PushToTalkConfig(
            stt_provider="openai",  # Set this to avoid Deepgram key validation
            refinement_provider="custom",
            custom_api_key="test-custom-key",
            custom_endpoint="http://localhost:11434/v1",
            openai_api_key="should-ignore-this",
            enable_text_refinement=True,
        )

        # We need to mock environment variables to avoid validation errors if keys aren't present
        mocker.patch.dict("os.environ", {"OPENAI_API_KEY": "env-key"})

        _ = PushToTalkApp(config=config)

        # Verify create_refiner was called with correct arguments
        mock_factory.create_refiner.assert_called_once()
        call_args = mock_factory.create_refiner.call_args
        assert call_args[1]["provider"] == "custom"
        assert call_args[1]["api_key"] == "test-custom-key"
        assert call_args[1]["base_url"] == "http://localhost:11434/v1"

    def test_text_refiner_factory_custom_creation(self, mocker):
        """Test that TextRefinerFactory creates TextRefinerOpenAI for custom provider."""
        from src.text_refiner_factory import TextRefinerFactory

        # Mock TextRefinerOpenAI
        mock_openai_refiner = mocker.patch("src.text_refiner_factory.TextRefinerOpenAI")

        _ = TextRefinerFactory.create_refiner(
            provider="custom",
            api_key="test-key",
            model="llama3",
            base_url="http://custom.url/v1",
        )

        mock_openai_refiner.assert_called_once_with(
            api_key="test-key", model="llama3", base_url="http://custom.url/v1"
        )

    def test_config_validation_custom_provider(self):
        """Test validation for custom provider."""
        # Valid
        config = PushToTalkConfig(refinement_provider="custom")
        assert config.refinement_provider == "custom"

        # Invalid
        with pytest.raises(ValueError):
            PushToTalkConfig(refinement_provider="invalid_provider")
