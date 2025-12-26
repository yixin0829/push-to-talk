"""Hotkey recording functionality for capturing key combinations from user input."""

import threading
from enum import Enum
from typing import Callable, Optional, Set

from pynput import keyboard as pynput_keyboard

from src.hotkey_service import HotkeyService


class RecordingState(Enum):
    """State of the hotkey recorder."""

    IDLE = "idle"
    RECORDING = "recording"


# Modifier keys in display order
MODIFIER_ORDER = ["ctrl", "alt", "shift", "cmd"]

# Shift+number to symbol mapping (US keyboard layout)
SHIFT_NUMBER_TO_SYMBOL = {
    "1": "!",
    "2": "@",
    "3": "#",
    "4": "$",
    "5": "%",
    "6": "^",
    "7": "&",
    "8": "*",
    "9": "(",
    "0": ")",
}


class HotkeyRecorder:
    """Records key combinations from user input.

    This class captures keyboard input using pynput and converts it to
    a hotkey string format compatible with HotkeyService.
    """

    # Stabilization delay in seconds before finalizing after all keys released
    STABILIZATION_DELAY = 0.3

    def __init__(
        self,
        on_recording_complete: Callable[[str], None],
        on_recording_cancelled: Callable[[], None],
        on_keys_changed: Callable[[str], None],
    ):
        """Initialize the hotkey recorder.

        Args:
            on_recording_complete: Called with normalized hotkey string when done
            on_recording_cancelled: Called when user cancels (Escape or timeout)
            on_keys_changed: Called with current combination during recording
        """
        self._on_recording_complete = on_recording_complete
        self._on_recording_cancelled = on_recording_cancelled
        self._on_keys_changed = on_keys_changed

        self._state = RecordingState.IDLE
        self._current_keys: Set[str] = set()
        self._captured_keys: Set[str] = set()  # Keys captured before release
        self._listener: Optional[pynput_keyboard.Listener] = None
        self._lock = threading.Lock()
        self._timeout_timer: Optional[threading.Timer] = None
        self._stabilization_timer: Optional[threading.Timer] = None

    @property
    def is_recording(self) -> bool:
        """Check if recorder is currently recording."""
        return self._state == RecordingState.RECORDING

    def start_recording(self, timeout_seconds: float = 10.0) -> bool:
        """Start listening for key presses.

        Args:
            timeout_seconds: Maximum time to wait for input before cancelling

        Returns:
            True if recording started, False if already recording
        """
        with self._lock:
            if self._state == RecordingState.RECORDING:
                return False

            self._state = RecordingState.RECORDING
            self._current_keys.clear()
            self._captured_keys.clear()

        # Start timeout timer
        self._timeout_timer = threading.Timer(timeout_seconds, self._on_timeout)
        self._timeout_timer.daemon = True
        self._timeout_timer.start()

        # Start keyboard listener
        self._listener = pynput_keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )
        self._listener.start()

        return True

    def stop_recording(self) -> None:
        """Stop recording and clean up resources."""
        self._cleanup()

    def _cleanup(self) -> None:
        """Clean up listener and timers."""
        with self._lock:
            self._state = RecordingState.IDLE

        if self._timeout_timer:
            self._timeout_timer.cancel()
            self._timeout_timer = None

        if self._stabilization_timer:
            self._stabilization_timer.cancel()
            self._stabilization_timer = None

        if self._listener:
            self._listener.stop()
            self._listener = None

    def _on_timeout(self) -> None:
        """Handle recording timeout."""
        self._cleanup()
        self._on_recording_cancelled()

    def _on_key_press(self, key) -> None:
        """Handle key press event."""
        if self._state != RecordingState.RECORDING:
            return

        # Cancel any pending stabilization
        if self._stabilization_timer:
            self._stabilization_timer.cancel()
            self._stabilization_timer = None

        # Convert key to normalized name
        key_name = self._key_to_name(key)
        if key_name is None:
            return

        # Check for Escape to cancel
        if key_name == "esc":
            self._cleanup()
            self._on_recording_cancelled()
            return

        with self._lock:
            self._current_keys.add(key_name)
            self._captured_keys.add(key_name)

        # Notify about current keys
        hotkey_string = self._format_hotkey_string(self._current_keys)
        self._on_keys_changed(hotkey_string)

    def _on_key_release(self, key) -> None:
        """Handle key release event."""
        if self._state != RecordingState.RECORDING:
            return

        key_name = self._key_to_name(key)
        if key_name is None:
            return

        with self._lock:
            self._current_keys.discard(key_name)
            all_released = len(self._current_keys) == 0
            has_captured = len(self._captured_keys) > 0

        # If all keys released and we captured something, start stabilization
        if all_released and has_captured:
            self._stabilization_timer = threading.Timer(
                self.STABILIZATION_DELAY, self._finalize_recording
            )
            self._stabilization_timer.daemon = True
            self._stabilization_timer.start()

    def _finalize_recording(self) -> None:
        """Finalize the recording with captured keys."""
        with self._lock:
            if self._state != RecordingState.RECORDING:
                return
            captured = self._captured_keys.copy()

        self._cleanup()

        if captured:
            hotkey_string = self._format_hotkey_string(captured)
            self._on_recording_complete(hotkey_string)
        else:
            self._on_recording_cancelled()

    def _key_to_name(self, key) -> Optional[str]:
        """Convert pynput key to normalized string name.

        Reuses HotkeyService normalization logic for consistency.
        """
        try:
            if isinstance(key, pynput_keyboard.Key):
                name = key.name
            elif isinstance(key, pynput_keyboard.KeyCode):
                if key.char:
                    name = key.char
                elif key.vk is not None:
                    # When Ctrl is held, key.char is often None.
                    # Map Shift+6 (vk=54) to caret on US keyboard layouts.
                    if key.vk == 54 and "shift" in self._current_keys:
                        name = "^"
                    else:
                        try:
                            mapped = pynput_keyboard.KeyCode.from_vk(key.vk)
                            if mapped.char:
                                name = mapped.char
                            elif hasattr(mapped, "name") and mapped.name:
                                name = mapped.name
                            else:
                                name = f"vk{key.vk}"
                        except Exception:
                            name = f"vk{key.vk}"
                else:
                    name = None
            else:
                name = getattr(key, "name", None) or getattr(key, "char", None)

            if name is None:
                return None

            # Keep symbols as-is (e.g., ^, !, @), normalize others (e.g., ctrl_l -> ctrl)
            if len(name) == 1 and not name.isalnum():
                return name

            return HotkeyService._normalize_key_name(str(name))

        except Exception:
            return None

    @staticmethod
    def _format_hotkey_string(keys: Set[str]) -> str:
        """Format keys as hotkey string with modifiers first.

        Args:
            keys: Set of normalized key names

        Returns:
            Hotkey string like "ctrl+shift+^"
        """
        if not keys:
            return ""

        # Work with a mutable copy
        keys = set(keys)

        # Convert Shift+number to symbol (e.g., shift+6 -> ^)
        if "shift" in keys:
            for number, symbol in SHIFT_NUMBER_TO_SYMBOL.items():
                if number in keys:
                    keys.discard(number)
                    keys.add(symbol)

        modifiers = []
        regular_keys = []

        for key in keys:
            if key in MODIFIER_ORDER:
                modifiers.append(key)
            else:
                regular_keys.append(key)

        # Sort modifiers by predefined order
        modifiers.sort(key=lambda k: MODIFIER_ORDER.index(k))

        # Sort regular keys alphabetically
        regular_keys.sort()

        return "+".join(modifiers + regular_keys)
