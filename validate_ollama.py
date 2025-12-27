#!/usr/bin/env python3
"""
Validation script for using local Ollama instance with the text refiner.
This script demonstrates how to configure the refiner to use Ollama's OpenAI-compatible API.

Prerequisites:
    - Ollama installed and running (default: http://localhost:11434)
    - A model pulled in Ollama (e.g., 'llama3' or 'mistral')
      Run `ollama pull llama3` before running this script if you haven't.

Usage:
    uv run python validate_ollama.py [model_name] [base_url]
"""

import sys
import os
from loguru import logger

from src.text_refiner_openai import TextRefinerOpenAI
from src.exceptions import ConfigurationError, TextRefinementError

def validate_ollama(model_name="llama3", base_url="http://localhost:11434/v1"):
    logger.info(f"Validating Ollama integration with model='{model_name}' and base_url='{base_url}'")

    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO")

    try:
        # Initialize the refiner with custom base_url for Ollama
        # Note: Ollama doesn't strictly require an API key, but the client expects one.
        # We can pass any string as the api_key.
        refiner = TextRefinerOpenAI(
            api_key="ollama",  # Placeholder key
            model=model_name,
            base_url=base_url
        )

        logger.info("Refiner initialized successfully.")

        # Test text to refine
        raw_text = "thsi is a tesst text that needz refinment it has speling erors and no punctuashun"
        logger.info(f"Original text: {raw_text}")

        # Perform refinement
        logger.info("Sending request to Ollama...")
        refined_text = refiner.refine_text(raw_text)

        if refined_text:
            logger.success("Refinement successful!")
            logger.info(f"Refined text: {refined_text}")
            return True
        else:
            logger.warning("Refinement returned empty text.")
            return False

    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        return False
    except TextRefinementError as e:
        logger.error(f"Refinement failed: {e}")
        logger.info("Tip: Make sure Ollama is running and the model is pulled (e.g., 'ollama pull llama3')")
        return False
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    # Get arguments from command line or use defaults
    model = sys.argv[1] if len(sys.argv) > 1 else "llama3"
    url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:11434/v1"

    success = validate_ollama(model, url)
    sys.exit(0 if success else 1)
