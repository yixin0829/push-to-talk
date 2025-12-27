from typing import Optional
from src.text_refiner_base import TextRefinerBase
from src.text_refiner_openai import TextRefinerOpenAI
from src.text_refiner_cerebras import CerebrasTextRefiner
from src.text_refiner_gemini import GeminiTextRefiner


class TextRefinerFactory:
    """Factory for creating text refiner instances based on provider."""

    @staticmethod
    def create_refiner(
        provider: str,
        api_key: str,
        model: str,
        glossary: Optional[list[str]] = None,
        base_url: Optional[str] = None,
    ) -> TextRefinerBase:
        """
        Create a text refiner instance based on the specified provider.

        Args:
            provider: The refinement provider ('openai', 'cerebras', or 'gemini')
            api_key: API key for the provider
            model: Model name to use for refinement
            glossary: Optional list of custom glossary terms
            base_url: Optional custom API endpoint URL (for OpenAI-compatible APIs)

        Returns:
            TextRefinerBase instance configured for the specified provider

        Raises:
            ValueError: If the provider is not supported
        """
        if provider == "openai":
            refiner = TextRefinerOpenAI(api_key=api_key, model=model, base_url=base_url)
        elif provider == "cerebras":
            refiner = CerebrasTextRefiner(api_key=api_key, model=model)
        elif provider == "gemini":
            refiner = GeminiTextRefiner(api_key=api_key, model=model)
        else:
            raise ValueError(
                f"Unsupported refinement provider: {provider}. "
                f"Supported providers: openai, cerebras, gemini"
            )

        # Set glossary if provided
        if glossary:
            refiner.set_glossary(glossary)

        return refiner
