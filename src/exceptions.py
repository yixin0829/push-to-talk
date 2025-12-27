"""Custom exceptions for PushToTalk application.

This module defines custom exception classes for consistent error handling
throughout the application. Using custom exceptions allows for:
- Better error categorization and handling
- More descriptive error messages
- Easier debugging and error tracking
"""


class PushToTalkError(Exception):
    """Base exception class for all PushToTalk errors."""

    pass


class AudioRecordingError(PushToTalkError):
    """Raised when audio recording fails."""

    pass


class TranscriptionError(PushToTalkError):
    """Raised when audio transcription fails."""

    pass


class TextRefinementError(PushToTalkError):
    """Raised when text refinement fails."""

    pass


class TextInsertionError(PushToTalkError):
    """Raised when text insertion into active window fails."""

    pass


class ConfigurationError(PushToTalkError):
    """Raised when configuration is invalid or missing required values."""

    pass


class APIError(PushToTalkError):
    """Raised when an API call fails (transcription or refinement)."""

    def __init__(self, message: str, provider: str = None, status_code: int = None):
        """
        Initialize API error with additional context.

        Args:
            message: Error message
            provider: API provider name (e.g., 'OpenAI', 'Deepgram')
            status_code: HTTP status code if applicable
        """
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code


class HotkeyError(PushToTalkError):
    """Raised when hotkey registration or handling fails."""

    pass
