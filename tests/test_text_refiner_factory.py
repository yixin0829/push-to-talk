import pytest
import os
from loguru import logger
from unittest.mock import MagicMock

from src.text_refiner_factory import TextRefinerFactory
from src.text_refiner_openai import TextRefinerOpenAI
from src.text_refiner_cerebras import CerebrasTextRefiner
from src.text_refiner_gemini import GeminiTextRefiner
from src.text_refiner_base import TextRefinerBase


class TestTextRefinerFactory:
    def test_create_openai_refiner(self, mocker):
        """Test factory creates OpenAI refiner"""
        logger.info("Testing factory creates OpenAI refiner")

        mocker.patch.dict(os.environ, {"OPENAI_API_KEY": "test-openai-key"})

        refiner = TextRefinerFactory.create_refiner(
            provider="openai", api_key="test-openai-key", model="gpt-4o-mini"
        )

        assert isinstance(refiner, TextRefinerOpenAI)
        assert isinstance(refiner, TextRefinerBase)
        assert refiner.api_key == "test-openai-key"
        assert refiner.model == "gpt-4o-mini"

        logger.info("Factory creates OpenAI refiner test passed")

    def test_create_openai_refiner_with_custom_model(self, mocker):
        """Test factory creates OpenAI refiner with custom model"""
        logger.info("Testing factory creates OpenAI refiner with custom model")

        mocker.patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})

        refiner = TextRefinerFactory.create_refiner(
            provider="openai", api_key="test-key", model="gpt-4o"
        )

        assert isinstance(refiner, TextRefinerOpenAI)
        assert refiner.model == "gpt-4o"

        logger.info("Factory creates OpenAI refiner with custom model test passed")

    def test_create_cerebras_refiner(self, mocker):
        """Test factory creates Cerebras refiner"""
        logger.info("Testing factory creates Cerebras refiner")

        mocker.patch.dict(os.environ, {"CEREBRAS_API_KEY": "test-cerebras-key"})
        mock_client = MagicMock()
        mocker.patch("src.text_refiner_cerebras.Cerebras", return_value=mock_client)

        refiner = TextRefinerFactory.create_refiner(
            provider="cerebras", api_key="test-cerebras-key", model="llama-3.3-70b"
        )

        assert isinstance(refiner, CerebrasTextRefiner)
        assert isinstance(refiner, TextRefinerBase)
        assert refiner.api_key == "test-cerebras-key"
        assert refiner.model == "llama-3.3-70b"

        logger.info("Factory creates Cerebras refiner test passed")

    def test_create_cerebras_refiner_with_custom_model(self, mocker):
        """Test factory creates Cerebras refiner with custom model"""
        logger.info("Testing factory creates Cerebras refiner with custom model")

        mocker.patch.dict(os.environ, {"CEREBRAS_API_KEY": "test-key"})
        mock_client = MagicMock()
        mocker.patch("src.text_refiner_cerebras.Cerebras", return_value=mock_client)

        refiner = TextRefinerFactory.create_refiner(
            provider="cerebras", api_key="test-key", model="llama-3.1-70b"
        )

        assert isinstance(refiner, CerebrasTextRefiner)
        assert refiner.model == "llama-3.1-70b"

        logger.info("Factory creates Cerebras refiner with custom model test passed")

    def test_invalid_provider_raises_error(self):
        """Test invalid provider raises ValueError"""
        logger.info("Testing invalid provider raises ValueError")

        with pytest.raises(ValueError) as exc_info:
            TextRefinerFactory.create_refiner(
                provider="invalid", api_key="test-key", model="test-model"
            )

        assert "Unsupported refinement provider" in str(exc_info.value)
        assert "invalid" in str(exc_info.value)

        logger.info("Invalid provider raises error test passed")

    def test_empty_provider_raises_error(self):
        """Test empty provider raises ValueError"""
        logger.info("Testing empty provider raises ValueError")

        with pytest.raises(ValueError) as exc_info:
            TextRefinerFactory.create_refiner(
                provider="", api_key="test-key", model="test-model"
            )

        assert "Unsupported refinement provider" in str(exc_info.value)

        logger.info("Empty provider raises error test passed")

    def test_case_sensitive_provider(self, mocker):
        """Test provider names are case-sensitive"""
        logger.info("Testing provider names are case-sensitive")

        mocker.patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})

        # Should fail with uppercase
        with pytest.raises(ValueError):
            TextRefinerFactory.create_refiner(
                provider="OPENAI", api_key="test-key", model="gpt-4o-mini"
            )

        with pytest.raises(ValueError):
            TextRefinerFactory.create_refiner(
                provider="OpenAI", api_key="test-key", model="gpt-4o-mini"
            )

        with pytest.raises(ValueError):
            TextRefinerFactory.create_refiner(
                provider="Cerebras", api_key="test-key", model="llama-3.3-70b"
            )

        logger.info("Case-sensitive provider test passed")

    def test_all_refiners_implement_base_interface(self, mocker):
        """Test that all refiners created by factory implement TextRefinerBase"""
        logger.info("Testing all refiners implement base interface")

        mocker.patch.dict(
            os.environ,
            {"OPENAI_API_KEY": "test-key", "CEREBRAS_API_KEY": "test-key"},
        )
        mock_client = MagicMock()
        mocker.patch("src.text_refiner_cerebras.Cerebras", return_value=mock_client)

        openai_refiner = TextRefinerFactory.create_refiner(
            provider="openai", api_key="test-key", model="gpt-4o-mini"
        )

        cerebras_refiner = TextRefinerFactory.create_refiner(
            provider="cerebras", api_key="test-key", model="llama-3.3-70b"
        )

        # Check they all implement the base interface
        assert isinstance(openai_refiner, TextRefinerBase)
        assert isinstance(cerebras_refiner, TextRefinerBase)

        # Check they all have the required methods
        assert hasattr(openai_refiner, "refine_text")
        assert hasattr(cerebras_refiner, "refine_text")
        assert callable(openai_refiner.refine_text)
        assert callable(cerebras_refiner.refine_text)

        assert hasattr(openai_refiner, "set_glossary")
        assert hasattr(cerebras_refiner, "set_glossary")
        assert callable(openai_refiner.set_glossary)
        assert callable(cerebras_refiner.set_glossary)

        logger.info("All refiners implement base interface test passed")

    def test_create_refiner_with_glossary(self, mocker):
        """Test factory creates refiner with glossary"""
        logger.info("Testing factory creates refiner with glossary")

        mocker.patch.dict(
            os.environ,
            {"OPENAI_API_KEY": "test-key", "CEREBRAS_API_KEY": "test-key"},
        )
        mock_client = MagicMock()
        mocker.patch("src.text_refiner_cerebras.Cerebras", return_value=mock_client)

        glossary = ["API", "OAuth", "Pydantic"]

        # Test with OpenAI refiner
        openai_refiner = TextRefinerFactory.create_refiner(
            provider="openai",
            api_key="test-key",
            model="gpt-4o-mini",
            glossary=glossary,
        )

        assert isinstance(openai_refiner, TextRefinerOpenAI)
        assert openai_refiner.glossary == glossary

        # Test with Cerebras refiner
        cerebras_refiner = TextRefinerFactory.create_refiner(
            provider="cerebras",
            api_key="test-key",
            model="llama-3.3-70b",
            glossary=glossary,
        )

        assert isinstance(cerebras_refiner, CerebrasTextRefiner)
        assert cerebras_refiner.glossary == glossary

        logger.info("Create refiner with glossary test passed")

    def test_create_refiner_without_glossary(self, mocker):
        """Test factory creates refiner without glossary"""
        logger.info("Testing factory creates refiner without glossary")

        mocker.patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})

        # Test without glossary parameter
        refiner = TextRefinerFactory.create_refiner(
            provider="openai", api_key="test-key", model="gpt-4o-mini"
        )

        assert isinstance(refiner, TextRefinerOpenAI)
        assert refiner.glossary == []

        logger.info("Create refiner without glossary test passed")

    def test_create_refiner_with_empty_glossary(self, mocker):
        """Test factory creates refiner with empty glossary"""
        logger.info("Testing factory creates refiner with empty glossary")

        mocker.patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})

        # Test with empty glossary
        refiner = TextRefinerFactory.create_refiner(
            provider="openai", api_key="test-key", model="gpt-4o-mini", glossary=[]
        )

        assert isinstance(refiner, TextRefinerOpenAI)
        assert refiner.glossary == []

        logger.info("Create refiner with empty glossary test passed")

    def test_create_gemini_refiner(self, mocker):
        """Test factory creates Gemini refiner"""
        logger.info("Testing factory creates Gemini refiner")

        mocker.patch.dict(os.environ, {"GOOGLE_API_KEY": "test-gemini-key"})
        mock_genai = MagicMock()
        mocker.patch("src.text_refiner_gemini.genai", mock_genai)

        refiner = TextRefinerFactory.create_refiner(
            provider="gemini", api_key="test-gemini-key", model="gemini-3-flash-preview"
        )

        assert isinstance(refiner, GeminiTextRefiner)
        assert isinstance(refiner, TextRefinerBase)
        assert refiner.api_key == "test-gemini-key"
        assert refiner.model == "gemini-3-flash-preview"

        logger.info("Factory creates Gemini refiner test passed")

    def test_create_gemini_refiner_with_custom_model(self, mocker):
        """Test factory creates Gemini refiner with custom model"""
        logger.info("Testing factory creates Gemini refiner with custom model")

        mocker.patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
        mock_genai = MagicMock()
        mocker.patch("src.text_refiner_gemini.genai", mock_genai)

        refiner = TextRefinerFactory.create_refiner(
            provider="gemini", api_key="test-key", model="gemini-2.5-pro-preview-06-05"
        )

        assert isinstance(refiner, GeminiTextRefiner)
        assert refiner.model == "gemini-2.5-pro-preview-06-05"

        logger.info("Factory creates Gemini refiner with custom model test passed")

    def test_create_openai_refiner_with_base_url(self, mocker):
        """Test factory creates OpenAI refiner with custom base URL"""
        logger.info("Testing factory creates OpenAI refiner with custom base URL")

        mocker.patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})

        refiner = TextRefinerFactory.create_refiner(
            provider="openai",
            api_key="test-key",
            model="gpt-4o-mini",
            base_url="https://custom-api.example.com/v1",
        )

        assert isinstance(refiner, TextRefinerOpenAI)
        assert refiner.base_url == "https://custom-api.example.com/v1"

        logger.info("Factory creates OpenAI refiner with base URL test passed")

    def test_create_openai_refiner_without_base_url(self, mocker):
        """Test factory creates OpenAI refiner without base URL (default)"""
        logger.info("Testing factory creates OpenAI refiner without base URL")

        mocker.patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})

        refiner = TextRefinerFactory.create_refiner(
            provider="openai", api_key="test-key", model="gpt-4o-mini"
        )

        assert isinstance(refiner, TextRefinerOpenAI)
        assert refiner.base_url is None

        logger.info("Factory creates OpenAI refiner without base URL test passed")

    def test_all_refiners_implement_base_interface_including_gemini(self, mocker):
        """Test that all refiners including Gemini implement TextRefinerBase"""
        logger.info("Testing all refiners including Gemini implement base interface")

        mocker.patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test-key",
                "CEREBRAS_API_KEY": "test-key",
                "GOOGLE_API_KEY": "test-key",
            },
        )
        mock_cerebras_client = MagicMock()
        mocker.patch(
            "src.text_refiner_cerebras.Cerebras", return_value=mock_cerebras_client
        )
        mock_genai = MagicMock()
        mocker.patch("src.text_refiner_gemini.genai", mock_genai)

        openai_refiner = TextRefinerFactory.create_refiner(
            provider="openai", api_key="test-key", model="gpt-4o-mini"
        )

        cerebras_refiner = TextRefinerFactory.create_refiner(
            provider="cerebras", api_key="test-key", model="llama-3.3-70b"
        )

        gemini_refiner = TextRefinerFactory.create_refiner(
            provider="gemini", api_key="test-key", model="gemini-3-flash-preview"
        )

        # Check they all implement the base interface
        assert isinstance(openai_refiner, TextRefinerBase)
        assert isinstance(cerebras_refiner, TextRefinerBase)
        assert isinstance(gemini_refiner, TextRefinerBase)

        # Check they all have the required methods
        for refiner in [openai_refiner, cerebras_refiner, gemini_refiner]:
            assert hasattr(refiner, "refine_text")
            assert callable(refiner.refine_text)
            assert hasattr(refiner, "set_glossary")
            assert callable(refiner.set_glossary)

        logger.info(
            "All refiners including Gemini implement base interface test passed"
        )
