import os
from loguru import logger
import time
from typing import Optional
from openai import OpenAI
from src.config.prompts import (
    text_refiner_prompt_wo_glossary,
    text_refiner_prompt_w_glossary,
)
from src.text_refiner_base import TextRefinerBase


class TextRefinerOpenAI(TextRefinerBase):
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4.1-nano"):
        """
        Initialize the text refiner with OpenAI API.

        Args:
            api_key: OpenAI API key. If None, will use OPENAI_API_KEY environment variable
            model: Refinement Model to use (default: gpt-4.1-nano)
        """
        super().__init__()

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter."
            )

        self.model = model
        self.client = OpenAI(api_key=self.api_key)

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
        if len(raw_text.strip()) < 20:
            logger.info("Text too short for refinement, returning as-is")
            return raw_text.strip()

        try:
            if self.custom_refinement_prompt:
                developer_prompt = self.custom_refinement_prompt
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

        except Exception as e:
            logger.error(f"Text refinement failed: {e}")
            logger.info("Falling back to original text")
            return raw_text.strip()

    def _get_default_developer_prompt(self) -> str:
        """
        Get the default developer prompt based on glossary availability.

        Returns:
            Formatted developer prompt string
        """
        if self.glossary:
            # Format glossary terms into a bullet list
            formatted_glossary = "\n".join(
                f"- {term}" for term in sorted(self.glossary, key=str.lower)
            )
            return text_refiner_prompt_w_glossary.format(
                custom_glossary=formatted_glossary
            )
        else:
            return text_refiner_prompt_wo_glossary
