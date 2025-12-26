from abc import ABC, abstractmethod
from typing import Optional
from loguru import logger
from src.config.prompts import (
    text_refiner_prompt_wo_glossary,
    text_refiner_prompt_w_glossary,
)


class TextRefinerBase(ABC):
    """Base class for text refinement providers."""

    def __init__(self):
        """Initialize the text refiner base class."""
        # Custom glossary for transcription refinement
        self.glossary = []

        # Custom refinement prompt (aka instructions) for transcription text refinement
        self.custom_refinement_prompt = None

    @abstractmethod
    def refine_text(self, raw_text: str) -> Optional[str]:
        """
        Refine the transcribed text.

        Args:
            raw_text: Raw transcribed text to refine

        Returns:
            Refined text or None if refinement failed
        """
        pass

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

    def _format_custom_prompt(self) -> str:
        """
        Format the custom prompt, substituting the glossary placeholder if present.

        Returns:
            Formatted custom prompt string with glossary substituted
        """
        prompt = self.custom_refinement_prompt
        if "{custom_glossary}" in prompt:
            if self.glossary:
                formatted_glossary = "\n".join(
                    f"- {term}" for term in sorted(self.glossary, key=str.lower)
                )
            else:
                formatted_glossary = "(No glossary terms configured)"
            prompt = prompt.replace("{custom_glossary}", formatted_glossary)
        return prompt
