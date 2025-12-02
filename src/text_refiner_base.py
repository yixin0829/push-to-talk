from abc import ABC, abstractmethod
from typing import Optional
from loguru import logger


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
        Should be implemented by subclasses if they use prompts.

        Returns:
            Formatted developer prompt string
        """
        raise NotImplementedError(
            "Subclass must implement _get_default_developer_prompt"
        )
