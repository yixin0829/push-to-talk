import time
from loguru import logger
import sys
from typing import Optional

import pyperclip
from pynput import keyboard

from src.config.constants import (
    TEXT_INSERTION_DELAY_AFTER_COPY_SECONDS,
    TEXT_INSERTION_DELAY_AFTER_PASTE_SECONDS,
)
from src.exceptions import TextInsertionError


class TextInserter:
    # Default insertion delay in seconds
    DEFAULT_INSERTION_DELAY = 0.005

    def __init__(self):
        """Initialize the text inserter."""
        self.insertion_delay = self.DEFAULT_INSERTION_DELAY
        self.keyboard = keyboard.Controller()

    def insert_text(self, text: str) -> bool:
        """
        Insert text into the currently active window using clipboard method.

        Args:
            text: Text to insert

        Returns:
            True if insertion was successful, False otherwise
        """
        if not text:
            logger.warning("Empty text provided for insertion")
            return False

        try:
            return self._insert_via_clipboard(text)
        except TextInsertionError:
            # Re-raise TextInsertionError as-is
            raise
        except Exception as e:
            logger.error(f"Text insertion failed: {e}")
            raise TextInsertionError(f"Failed to insert text: {e}") from e

    def _insert_via_clipboard(self, text: str) -> bool:
        """Insert text by copying to clipboard and pasting."""

        try:
            original_clipboard = pyperclip.paste()
            pyperclip.copy(text)

            time.sleep(TEXT_INSERTION_DELAY_AFTER_COPY_SECONDS)

            # Use platform-specific modifier key for paste
            modifier_key = (
                keyboard.Key.cmd if sys.platform == "darwin" else keyboard.Key.ctrl
            )

            # Press modifier+v to paste
            with self.keyboard.pressed(modifier_key):
                self.keyboard.press("v")
                self.keyboard.release("v")

            time.sleep(TEXT_INSERTION_DELAY_AFTER_PASTE_SECONDS)

            if original_clipboard:
                pyperclip.copy(original_clipboard)

            logger.info(f"Text inserted via clipboard: {len(text)} characters")
            return True

        except Exception as e:
            logger.error(f"Clipboard insertion failed: {e}")
            raise TextInsertionError(f"Clipboard insertion failed: {e}") from e

    def _get_clipboard_text(self) -> Optional[str]:
        """Get current clipboard text content."""
        try:
            return pyperclip.paste()
        except Exception:
            return None

    def _set_clipboard_text(self, text: str) -> None:
        """Set clipboard text content."""
        pyperclip.copy(text)

    def get_active_window_title(self) -> Optional[str]:
        """
        Get the title of the currently active window.

        Note: This functionality is not available without pyautogui.
        Returns None for logging purposes.

        Returns:
            None (window title detection not implemented)
        """
        # Window title detection was removed to eliminate pyautogui dependency
        # This is only used for logging, so returning None is acceptable
        return None
