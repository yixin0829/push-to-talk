import keyboard
import threading
import logging
import sys
from typing import Callable, Optional, Set
import time

logger = logging.getLogger(__name__)


class HotkeyService:
    def __init__(self, hotkey: str = None, toggle_hotkey: str = None):
        """
        Initialize the hotkey service.

        Args:
            hotkey: Hotkey combination for push-to-talk (default: platform-specific)
            toggle_hotkey: Hotkey combination for toggle recording (default: platform-specific)
        """
        # Set platform-specific default hotkeys if none provided
        self.hotkey = hotkey or self._get_default_hotkey()
        self.toggle_hotkey = toggle_hotkey or self._get_default_toggle_hotkey()
        self.is_running = False
        self.is_recording = False
        self.is_toggle_mode = False  # Track if currently recording via toggle mode
        self.service_thread: Optional[threading.Thread] = None

        # Track which keys are currently pressed for the hotkey combination
        self.pressed_keys: Set[str] = set()
        self.hotkey_keys: Set[str] = set()
        self.toggle_hotkey_keys: Set[str] = set()

        # Callbacks
        self.on_start_recording: Optional[Callable] = None
        self.on_stop_recording: Optional[Callable] = None

        # Lock for thread-safe operations
        self._lock = threading.Lock()

        # Parse both hotkeys to get individual keys
        self._parse_hotkeys()

    @staticmethod
    def _get_platform_modifier() -> str:
        """Get the primary modifier key for the current platform."""
        return "cmd" if sys.platform == "darwin" else "ctrl"

    @staticmethod
    def _get_default_hotkey() -> str:
        """Get the default push-to-talk hotkey for the current platform."""
        modifier = HotkeyService._get_platform_modifier()
        return f"{modifier}+shift+space"

    @staticmethod
    def _get_default_toggle_hotkey() -> str:
        """Get the default toggle hotkey for the current platform."""
        modifier = HotkeyService._get_platform_modifier()
        return f"{modifier}+shift+^"

    @staticmethod
    def get_platform_name() -> str:
        """Get a human-readable platform name."""
        if sys.platform == "darwin":
            return "macOS"
        elif sys.platform.startswith("linux"):
            return "Linux"
        elif sys.platform == "win32":
            return "Windows"
        else:
            return sys.platform

    def _parse_hotkeys(self):
        """Parse both hotkey strings to extract individual keys."""
        # Parse push-to-talk hotkey
        self._parse_hotkey_combination(self.hotkey, self.hotkey_keys)
        # Parse toggle hotkey
        self._parse_hotkey_combination(self.toggle_hotkey, self.toggle_hotkey_keys)

    def _parse_hotkey_combination(self, hotkey: str, key_set: Set[str]):
        """Parse a hotkey string to extract individual keys into the given set."""
        try:
            # Parse the hotkey combination to get individual keys
            parsed = keyboard.parse_hotkey(hotkey)
            key_set.clear()

            for combo in parsed:
                for key in combo:
                    # Convert scan codes to key names
                    if hasattr(key, "name"):
                        key_set.add(key.name)
                    else:
                        # Handle scan codes
                        key_name = (
                            keyboard.key_to_scan_codes(key)[0]
                            if isinstance(key, str)
                            else key
                        )
                        key_set.add(str(key_name))

            logger.info(f"Hotkey '{hotkey}' keys parsed: {key_set}")
        except Exception as e:
            logger.error(f"Error parsing hotkey '{hotkey}': {e}")
            # Fallback to manual parsing for common combinations
            modifier = self._get_platform_modifier()
            default_hotkey = f"{modifier}+shift+space"
            default_toggle = f"{modifier}+shift+^"

            if hotkey == default_hotkey:
                key_set.update({modifier, "shift", "space"})
            elif hotkey == default_toggle:
                key_set.update({modifier, "shift", "^"})
            elif hotkey == "cmd+shift+space":  # macOS support
                key_set.update({"cmd", "shift", "space"})
            elif hotkey == "cmd+shift+^":  # macOS support
                key_set.update({"cmd", "shift", "^"})

    def _parse_hotkey(self):
        """Parse the hotkey string to extract individual keys."""
        # This method is kept for backward compatibility but now calls the new method
        self._parse_hotkey_combination(self.hotkey, self.hotkey_keys)

    def set_callbacks(self, on_start_recording: Callable, on_stop_recording: Callable):
        """
        Set callback functions for recording start and stop events.

        Args:
            on_start_recording: Function to call when recording starts
            on_stop_recording: Function to call when recording stops
        """
        self.on_start_recording = on_start_recording
        self.on_stop_recording = on_stop_recording

    def start_service(self) -> bool:
        """
        Start the hotkey listening service.

        Returns:
            True if service started successfully, False otherwise
        """
        if self.is_running:
            logger.warning("Hotkey service is already running")
            return False

        if not self.on_start_recording or not self.on_stop_recording:
            logger.error("Callbacks must be set before starting service")
            return False

        try:
            self.is_running = True
            self.service_thread = threading.Thread(
                target=self._run_service, daemon=True
            )
            self.service_thread.start()

            platform_name = self.get_platform_name()
            logger.info(
                f"Hotkey service started on {platform_name}. "
                f"Press and hold '{self.hotkey}' to record, '{self.toggle_hotkey}' to toggle."
            )
            return True

        except Exception as e:
            logger.error(f"Failed to start hotkey service: {e}")
            self.is_running = False
            return False

    def stop_service(self):
        """Stop the hotkey listening service."""
        if not self.is_running:
            logger.warning("Hotkey service is not running")
            return

        self.is_running = False

        # Stop any ongoing recording
        if self.is_recording:
            self._stop_recording()

        # Unhook all keyboard events
        try:
            keyboard.unhook_all()
        except Exception as e:
            logger.warning(f"Error unhooking keyboard events: {e}")

        # Wait for service thread to finish
        if self.service_thread and self.service_thread.is_alive():
            self.service_thread.join(timeout=5.0)

        logger.info("Hotkey service stopped")

    def _run_service(self):
        """Main service loop running in a separate thread."""
        try:
            # Register both hotkey combinations
            keyboard.add_hotkey(self.hotkey, self._on_hotkey_press)
            keyboard.add_hotkey(self.toggle_hotkey, self._on_toggle_hotkey_press)

            # Register key release detection for push-to-talk keys only
            keyboard.on_release(self._on_key_release)

            # Keep the service running
            while self.is_running:
                time.sleep(0.1)

        except Exception as e:
            logger.error(f"Error in hotkey service: {e}")
        finally:
            # Clean up
            try:
                keyboard.unhook_all()
            except Exception:
                pass

    def _on_hotkey_press(self):
        """Handle push-to-talk hotkey combination press event."""
        with self._lock:
            if not self.is_recording and self.is_running:
                self._start_recording(toggle_mode=False)

    def _on_toggle_hotkey_press(self):
        """Handle toggle hotkey combination press event."""
        with self._lock:
            if not self.is_running:
                return

            if self.is_recording:
                # Currently recording, stop it
                self._stop_recording()
            else:
                # Not recording, start it in toggle mode
                self._start_recording(toggle_mode=True)

    def _on_key_release(self, event):
        """Handle any key release event for push-to-talk mode only."""
        with self._lock:
            # Only handle key release if we're in push-to-talk mode (not toggle mode)
            if self.is_recording and self.is_running and not self.is_toggle_mode:
                # Check if any of the push-to-talk hotkey keys was released
                key_name = (
                    event.name if hasattr(event, "name") else str(event.scan_code)
                )

                # Check common key name variations
                key_variations = [key_name]
                if key_name == "left ctrl" or key_name == "right ctrl":
                    key_variations.extend(["ctrl", "left ctrl", "right ctrl"])
                elif key_name == "left shift" or key_name == "right shift":
                    key_variations.extend(["shift", "left shift", "right shift"])
                elif key_name == "ctrl":
                    key_variations.extend(["left ctrl", "right ctrl"])
                elif key_name == "shift":
                    key_variations.extend(["left shift", "right shift"])
                # macOS command key variations
                elif key_name == "left cmd" or key_name == "right cmd":
                    key_variations.extend(["cmd", "left cmd", "right cmd", "command"])
                elif key_name == "cmd" or key_name == "command":
                    key_variations.extend(["left cmd", "right cmd", "cmd", "command"])

                # If any variation of the released key is part of our push-to-talk hotkey, stop recording
                if any(
                    var in self.hotkey_keys or var == "space" for var in key_variations
                ):
                    self._stop_recording()

    def _start_recording(self, toggle_mode: bool = False):
        """Start recording audio.

        Args:
            toggle_mode: True if started via toggle hotkey, False if push-to-talk
        """
        try:
            if self.on_start_recording:
                self.is_recording = True
                self.is_toggle_mode = toggle_mode
                mode_str = "toggle" if toggle_mode else "push-to-talk"
                logger.info(f"Recording started ({mode_str} mode)")
                self.on_start_recording()
        except Exception as e:
            logger.error(f"Error starting recording: {e}")
            self.is_recording = False
            self.is_toggle_mode = False

    def _stop_recording(self):
        """Stop recording audio."""
        try:
            if self.on_stop_recording and self.is_recording:
                mode_str = "toggle" if self.is_toggle_mode else "push-to-talk"
                self.is_recording = False
                self.is_toggle_mode = False
                logger.info(f"Recording stopped ({mode_str} mode)")
                self.on_stop_recording()
        except Exception as e:
            logger.error(f"Error stopping recording: {e}")

    def change_hotkey(self, new_hotkey: str) -> bool:
        """
        Change the push-to-talk hotkey combination.

        Args:
            new_hotkey: New hotkey combination

        Returns:
            True if hotkey was changed successfully, False otherwise
        """
        was_running = self.is_running

        if was_running:
            self.stop_service()

        try:
            # Test if the hotkey is valid
            keyboard.parse_hotkey(new_hotkey)
            self.hotkey = new_hotkey
            self._parse_hotkey_combination(
                self.hotkey, self.hotkey_keys
            )  # Re-parse the new hotkey

            if was_running:
                return self.start_service()

            logger.info(f"Push-to-talk hotkey changed to: {new_hotkey}")
            return True

        except Exception as e:
            logger.error(f"Invalid push-to-talk hotkey '{new_hotkey}': {e}")

            # Restore service if it was running
            if was_running:
                self.start_service()

            return False

    def change_toggle_hotkey(self, new_toggle_hotkey: str) -> bool:
        """
        Change the toggle hotkey combination.

        Args:
            new_toggle_hotkey: New toggle hotkey combination

        Returns:
            True if toggle hotkey was changed successfully, False otherwise
        """
        was_running = self.is_running

        if was_running:
            self.stop_service()

        try:
            # Test if the toggle hotkey is valid
            keyboard.parse_hotkey(new_toggle_hotkey)
            self.toggle_hotkey = new_toggle_hotkey
            self._parse_hotkey_combination(
                self.toggle_hotkey, self.toggle_hotkey_keys
            )  # Re-parse the new toggle hotkey

            if was_running:
                return self.start_service()

            logger.info(f"Toggle hotkey changed to: {new_toggle_hotkey}")
            return True

        except Exception as e:
            logger.error(f"Invalid toggle hotkey '{new_toggle_hotkey}': {e}")

            # Restore service if it was running
            if was_running:
                self.start_service()

            return False

    def get_hotkey(self) -> str:
        """
        Get the current push-to-talk hotkey combination.

        Returns:
            Current push-to-talk hotkey string
        """
        return self.hotkey

    def get_toggle_hotkey(self) -> str:
        """
        Get the current toggle hotkey combination.

        Returns:
            Current toggle hotkey string
        """
        return self.toggle_hotkey

    def is_toggle_recording(self) -> bool:
        """
        Check if currently recording in toggle mode.

        Returns:
            True if recording in toggle mode, False otherwise
        """
        return self.is_recording and self.is_toggle_mode

    def get_recording_mode(self) -> str:
        """
        Get the current recording mode.

        Returns:
            "toggle" if in toggle mode, "push-to-talk" if in push-to-talk mode, "idle" if not recording
        """
        if not self.is_recording:
            return "idle"
        return "toggle" if self.is_toggle_mode else "push-to-talk"

    def is_service_running(self) -> bool:
        """
        Check if the hotkey service is currently running.

        Returns:
            True if service is running, False otherwise
        """
        return self.is_running

    @staticmethod
    def get_platform_default_hotkey() -> str:
        """
        Get the default push-to-talk hotkey for the current platform.

        Returns:
            Default push-to-talk hotkey string for current platform
        """
        return HotkeyService._get_default_hotkey()

    @staticmethod
    def get_platform_default_toggle_hotkey() -> str:
        """
        Get the default toggle hotkey for the current platform.

        Returns:
            Default toggle hotkey string for current platform
        """
        return HotkeyService._get_default_toggle_hotkey()

    @staticmethod
    def get_platform_modifier_key() -> str:
        """
        Get the primary modifier key for the current platform.

        Returns:
            "cmd" for macOS, "ctrl" for Windows/Linux
        """
        return HotkeyService._get_platform_modifier()
