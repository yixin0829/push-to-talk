import os
from loguru import logger
import time
from typing import Optional
from cerebras.cloud.sdk import Cerebras
from src.text_refiner_base import TextRefinerBase
from src.exceptions import ConfigurationError, TextRefinementError, APIError
from src.config.constants import TEXT_REFINEMENT_MIN_LENGTH


class CerebrasTextRefiner(TextRefinerBase):
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b"):
        """
        Initialize the text refiner with Cerebras API.

        Args:
            api_key: Cerebras API key. If None, will use CEREBRAS_API_KEY environment variable
            model: Refinement Model to use (default: llama-3.3-70b)
        """
        super().__init__()

        self.api_key = api_key or os.getenv("CEREBRAS_API_KEY")
        if not self.api_key:
            raise ConfigurationError(
                "Cerebras API key is required. Set CEREBRAS_API_KEY environment variable or pass api_key parameter."
            )

        self.model = model
        self.client = Cerebras(api_key=self.api_key)

    def refine_text(self, raw_text: str) -> Optional[str]:
        """
        Refine the transcribed text using Cerebras model.

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
                system_prompt = self._format_custom_prompt()
            else:
                system_prompt = self._get_default_developer_prompt()

            # Start timing the LLM completion
            start_time = time.time()
            logger.info("Starting Cerebras LLM completion for text refinement")

            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Please refine this transcribed text:\n\n{raw_text}",
                    },
                ],
                model=self.model,
                stream=False,
                max_completion_tokens=2048,
                temperature=0.2,
                top_p=1,
            )

            # Calculate and log completion time
            completion_time = time.time() - start_time
            logger.info(
                f"Cerebras LLM completion finished in {completion_time:.2f} seconds"
            )

            refined_text = response.choices[0].message.content

            if not refined_text:
                logger.warning("Cerebras returned empty response, using original text")
                return raw_text.strip()

            logger.info(
                f"Text refinement successful: {len(raw_text)} -> {len(refined_text)} characters"
            )
            return refined_text

        except Exception as e:
            # Check if it's a Cerebras API error (would have status_code attribute)
            if hasattr(e, "status_code"):
                logger.error(f"Cerebras API error during text refinement: {e}")
                raise APIError(
                    f"Cerebras refinement API failed: {e}",
                    provider="Cerebras",
                    status_code=getattr(e, "status_code", None),
                ) from e
            else:
                logger.error(f"Text refinement failed: {e}")
                raise TextRefinementError(f"Failed to refine text: {e}") from e
