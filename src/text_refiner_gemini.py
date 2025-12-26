import os
from loguru import logger
import time
from typing import Optional
import google.generativeai as genai
from src.text_refiner_base import TextRefinerBase


class GeminiTextRefiner(TextRefinerBase):
    def __init__(
        self, api_key: Optional[str] = None, model: str = "gemini-3-flash-preview"
    ):
        """
        Initialize the text refiner with Google Gemini API.

        Args:
            api_key: Google Gemini API key. If None, will use GOOGLE_API_KEY environment variable
            model: Refinement Model to use (default: gemini-3-flash-preview)
        """
        super().__init__()

        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Google Gemini API key is required. Set GOOGLE_API_KEY environment variable or pass api_key parameter."
            )

        self.model = model
        genai.configure(api_key=self.api_key)
        self.client = genai.GenerativeModel(model_name=self.model)

    def refine_text(self, raw_text: str) -> Optional[str]:
        """
        Refine the transcribed text using Google Gemini model.

        Args:
            raw_text: Raw transcribed text to refine

        Returns:
            Refined text or None if refinement failed
        """
        if not raw_text or not raw_text.strip():
            logger.warning("Empty or blank text provided for refinement")
            return None

        # Skip refinement if too short (likely not worth the API call)
        if len(raw_text.strip()) < 20:
            logger.info("Text too short for refinement, returning as-is")
            return raw_text.strip()

        try:
            if self.custom_refinement_prompt:
                system_prompt = self._format_custom_prompt()
            else:
                system_prompt = self._get_default_developer_prompt()

            # Start timing the LLM completion
            start_time = time.time()
            logger.info("Starting Gemini LLM completion for text refinement")

            # Combine system prompt and user message
            full_prompt = f"{system_prompt}\n\nPlease refine this transcribed text:\n\n{raw_text}"

            response = self.client.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=2048,
                ),
            )

            # Calculate and log completion time
            completion_time = time.time() - start_time
            logger.info(
                f"Gemini LLM completion finished in {completion_time:.2f} seconds"
            )

            refined_text = response.text

            if not refined_text:
                logger.warning("Gemini returned empty response, using original text")
                return raw_text.strip()

            logger.info(
                f"Text refinement successful: {len(raw_text)} -> {len(refined_text)} characters"
            )
            return refined_text

        except Exception as e:
            logger.error(f"Text refinement failed: {e}")
            logger.info("Falling back to original text")
            return raw_text.strip()
