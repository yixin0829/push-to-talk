"""Validation logic for PushToTalk configuration."""

import urllib.request
import urllib.error
from src.push_to_talk import PushToTalkConfig


def validate_configuration(config: PushToTalkConfig) -> tuple[bool, str | None]:
    """
    Validate a configuration object.

    Args:
        config: Configuration object to validate

    Returns:
        Tuple of (is_valid, error_message). error_message is None if valid.
    """
    # Check API key based on selected provider
    if config.stt_provider == "openai":
        if not config.openai_api_key.strip():
            return (
                False,
                "OpenAI API key is required when using OpenAI provider!\n\n"
                "Please enter your OpenAI API key or switch to Deepgram provider.",
            )
    elif config.stt_provider == "deepgram":
        if not config.deepgram_api_key.strip():
            return (
                False,
                "Deepgram API key is required when using Deepgram provider!\n\n"
                "Please enter your Deepgram API key or switch to OpenAI provider.",
            )
    else:
        return False, f"Unknown provider: {config.stt_provider}"

    # Check hotkeys are different
    if config.hotkey == config.toggle_hotkey:
        return False, "Push-to-talk and toggle hotkeys must be different!"

    return True, None


def validate_openai_api_key(api_key: str) -> bool:
    """
    Validate OpenAI API key by making a test request.

    Args:
        api_key: OpenAI API key to validate

    Returns:
        True if valid, False otherwise

    Raises:
        Exception: With descriptive error message
    """
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        # Test the API key by listing models (lightweight operation)
        _ = client.models.list()
        return True
    except Exception as e:
        error_msg = str(e)
        # Extract the most relevant error message
        if "401" in error_msg or "Incorrect API key" in error_msg:
            raise Exception("INVALID - Incorrect API key")
        elif "404" in error_msg:
            raise Exception("INVALID - API endpoint not found")
        elif "timeout" in error_msg.lower():
            raise Exception("TIMEOUT - Network issue")
        else:
            raise Exception(f"ERROR - {error_msg[:60]}...")


def validate_deepgram_api_key(api_key: str) -> bool:
    """
    Validate Deepgram API key by making a direct request to the auth endpoint.

    Args:
        api_key: Deepgram API key to validate

    Returns:
        True if valid, False otherwise

    Raises:
        Exception: With error message containing HTTP error codes (401, 404) or timeout
    """
    url = "https://api.deepgram.com/v1/auth/token"
    headers = {"Authorization": f"Token {api_key}"}

    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=10):
            # If we get here, the API key is valid
            return True
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise Exception("401 - Incorrect API key")
        elif e.code == 404:
            raise Exception("404 - API endpoint not found")
        else:
            raise Exception(f"HTTP {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        raise Exception(f"timeout - Network error: {e.reason}")
