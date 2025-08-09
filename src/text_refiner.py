import os
import logging
import time
from typing import Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


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

        # Default developer prompt (aka instructions) for transcription text refinement
        self.developer_prompt = """Role and Objective
- Enhance transcribed speech-to-text outputs by refining them for clarity, accuracy, and format compliance.

Instructions
- Add appropriate punctuation and capitalization.
- Remove filler and unnecessary stop words.
- Improve grammar and sentence structure for optimal readability and clarity.
- Ensure the original meaning and intent of the message are preserved.
- If a user-provided format instruction is present at the end of the transcribed text, apply it to the refined output, but do not include the instruction in the final text.
- Do not introduce content that is not implied in the original input.
- Return only the refined text, without explanations or commentary.

Output Format
- Output only the refined text as a single string."""

    def refine_text(
        self, raw_text: str, custom_prompt: Optional[str] = None
    ) -> Optional[str]:
        """
        Refine the transcribed text using Refinement Model.

        Args:
            raw_text: Raw transcribed text to refine
            custom_prompt: Optional custom system prompt to override default

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
            developer_prompt = custom_prompt or self.developer_prompt

            # Start timing the LLM completion
            start_time = time.time()
            logger.info("Starting LLM completion for text refinement")

            settings = {"temperature": 0.3}
            if self.model.startswith("gpt-5"):
                settings["reasoning"] = {"effort": "minimal"}

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

    def set_custom_prompt(self, prompt: str):
        """
        Set a custom system prompt for text refinement.

        Args:
            prompt: Custom system prompt for the refiner
        """
        self.developer_prompt = prompt
        logger.info("Custom refinement prompt set")

    def get_current_prompt(self) -> str:
        """
        Get the current system prompt.

        Returns:
            Current system prompt string
        """
        return self.developer_prompt
