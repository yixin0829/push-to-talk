import os
from loguru import logger
import time
from typing import Optional
from openai import OpenAI, APIError as OpenAIAPIError
from src.text_refiner_base import TextRefinerBase
from src.exceptions import ConfigurationError, TextRefinementError, APIError
from src.config.constants import TEXT_REFINEMENT_MIN_LENGTH


class TextRefinerOpenAI(TextRefinerBase):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4.1-nano",
        base_url: Optional[str] = None,
    ):
        """
        Initialize the text refiner with OpenAI API.

        Args:
            api_key: OpenAI API key. If None, will use OPENAI_API_KEY environment variable
            model: Refinement Model to use (default: gpt-4.1-nano)
            base_url: Optional custom API endpoint URL (for OpenAI-compatible APIs)

        Raises:
            ConfigurationError: If API key is not provided
        """
        super().__init__()

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ConfigurationError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter."
            )

        self.model = model
        self.base_url = base_url if base_url else None

        # Create client with optional custom base URL
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
            logger.info(f"Using custom API endpoint: {self.base_url}")
        self.client = OpenAI(**client_kwargs)

    def refine_text(self, raw_text: str) -> Optional[str]:
        """
        Refine the transcribed text using Refinement Model.

        Args:
            raw_text: Raw transcribed text to refine

        Returns:
            Refined text or None if refinement failed
        """
        if not raw_text or not raw_text.strip():
            logger.warning("Empty or blank text provided for refinement")
            return None

        # Skip refinement if too short (likely not worth the API call)
        if len(raw_text.strip()) < TEXT_REFINEMENT_MIN_LENGTH:
            logger.info("Text too short for refinement, returning as-is")
            return raw_text.strip()

        try:
            if self.custom_refinement_prompt:
                developer_prompt = self._format_custom_prompt()
            else:
                developer_prompt = self._get_default_developer_prompt()

            # Start timing the LLM completion
            start_time = time.time()
            logger.info("Starting LLM completion for text refinement")

            settings = {}
            if self.model.startswith("gpt-5"):
                settings["reasoning"] = {"effort": "minimal"}
            else:
                settings["temperature"] = 0.3

            response = self.client.responses.create(
                model=self.model,
                instructions=developer_prompt,
                input=f"Please refine this transcribed text:\n\n{raw_text}",
                **settings,
            )

            # Calculate and log completion time
            completion_time = time.time() - start_time
            logger.info(f"LLM completion finished in {completion_time:.2f} seconds")

            refined_text = response.output_text

            if not refined_text:
                logger.warning("GPT returned empty response, using original text")
                return raw_text.strip()

            logger.info(
                f"Text refinement successful: {len(raw_text)} -> {len(refined_text)} characters"
            )
            return refined_text

        except OpenAIAPIError as e:
            logger.error(f"OpenAI API error during text refinement: {e}")
            raise APIError(
                f"OpenAI refinement API failed: {e}",
                provider="OpenAI",
                status_code=getattr(e, "status_code", None),
            ) from e
        except Exception as e:
            logger.error(f"Text refinement failed: {e}")
            raise TextRefinementError(f"Failed to refine text: {e}") from e
