import os
from loguru import logger
import time
from typing import Optional
from openai import OpenAI
from src.config.prompts import (
    text_refiner_prompt_wo_glossary,
    text_refiner_prompt_w_glossary,
)


class TextRefiner:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4.1-nano"):
        """
        Initialize the text refiner with OpenAI API.

        Args:
            api_key: OpenAI API key. If None, will use OPENAI_API_KEY environment variable
            model: Refinement Model to use (default: gpt-4.1-nano)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter."
            )

        self.model = model
        self.client = OpenAI(api_key=self.api_key)

        # Custom glossary for transcription refinement
        self.glossary = []

        # Custom refinement prompt (aka instructions) for transcription text refinement
        self.custom_refinement_prompt = None

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
            logger.debug(
                f"Starting LLM completion for text refinement - Model: {self.model}, Input length: {len(raw_text)} chars"
            )

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
            refined_text = response.output_text

            if not refined_text:
                logger.warning(
                    f"GPT returned empty response after {completion_time:.2f}s, using original text"
                )
                return raw_text.strip()

            # Calculate refinement metrics
            compression_ratio = (
                len(refined_text) / len(raw_text) if len(raw_text) > 0 else 1.0
            )
            chars_per_second = (
                len(refined_text) / completion_time if completion_time > 0 else 0
            )

            logger.info(
                f"Text refinement completed in {completion_time:.2f}s: {len(raw_text)} -> {len(refined_text)} chars "
                f"({compression_ratio:.2f}x, {chars_per_second:.1f} chars/s)"
            )
            return refined_text

        except Exception as e:
            completion_time = time.time() - start_time
            logger.error(f"Text refinement failed after {completion_time:.2f}s: {e}")
            logger.error(
                f"Refinement context - Model: {self.model}, Text length: {len(raw_text)} chars"
            )

            # Provide helpful error context
            if "API" in str(e) or "connection" in str(e).lower():
                logger.error(
                    "API connection error. Check internet connectivity and API key."
                )
            elif "rate" in str(e).lower() or "quota" in str(e).lower():
                logger.error(
                    "API rate limit or quota exceeded. Consider reducing refinement frequency."
                )

            logger.info("Falling back to original text")
            return raw_text.strip()

    def set_custom_prompt(self, prompt: str):
        """
        Set a custom system prompt for text refinement.

        Args:
            prompt: Custom system prompt for the refiner
        """
        self.custom_refinement_prompt = prompt
        logger.info(f"Custom refinement prompt set to:\n{prompt}")

    def get_current_prompt(self) -> str:
        """
        Get the current system prompt.

        Returns:
            Current system prompt string
        """
        return self.custom_refinement_prompt

    def set_glossary(self, glossary: list[str]):
        """
        Set the custom glossary for transcription refinement.

        Args:
            glossary: List of domain-specific terms, acronyms, and technical words
        """
        self.glossary = glossary if glossary else []
        logger.info(f"Glossary updated with {len(self.glossary)} terms")

    def get_glossary(self) -> list[str]:
        """
        Get the current custom glossary.

        Returns:
            List of glossary terms
        """
        return self.glossary.copy()

    def clear_glossary(self):
        """Clear the custom glossary."""
        self.glossary = []
        logger.info("Glossary cleared")

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
