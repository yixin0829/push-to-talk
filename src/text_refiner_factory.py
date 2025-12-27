from typing import Optional
from src.text_refiner_base import TextRefinerBase


class TextRefinerFactory:
    """Factory for creating text refiner instances based on provider."""

    @staticmethod
    def create_refiner(
        provider: str,
        api_key: str,
        model: str,
        glossary: Optional[list[str]] = None,
    ) -> TextRefinerBase:
        """
        Create a text refiner instance based on the specified provider.

        Args:
            provider: The refinement provider ('openai' or 'cerebras')
            api_key: API key for the provider
            model: Model name to use for refinement
            glossary: Optional list of custom glossary terms

        Returns:
            TextRefinerBase instance configured for the specified provider

        Raises:
            ValueError: If the provider is not supported
        """
        if provider == "openai":
            from src.text_refiner_openai import TextRefinerOpenAI

            refiner = TextRefinerOpenAI(api_key=api_key, model=model)
        elif provider == "cerebras":
            from src.text_refiner_cerebras import CerebrasTextRefiner

            refiner = CerebrasTextRefiner(api_key=api_key, model=model)
        else:
            raise ValueError(
                f"Unsupported refinement provider: {provider}. "
                f"Supported providers: openai, cerebras"
            )

        # Set glossary if provided
        if glossary:
            refiner.set_glossary(glossary)

        return refiner
