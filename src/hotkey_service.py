import threading
import time
import sys
import json
import functools
from pathlib import Path
from typing import Callable, Optional, Set

from loguru import logger
from pynput import keyboard as pynput_keyboard


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
        self.current_keys: Set[str] = set()
        self.hotkey_keys: Set[str] = set()
        self.toggle_hotkey_keys: Set[str] = set()

        # Track listener state
        self._listener: Optional[pynput_keyboard.Listener] = None
        self._push_hotkey_active = False
        self._toggle_hotkey_active = False

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
        key_set.clear()

        if not hotkey:
            return

        parts = [part.strip() for part in hotkey.split("+") if part.strip()]
        if not parts:
            logger.error(f"Hotkey '{hotkey}' did not contain any valid keys")
            return

        for raw_part in parts:
            normalized = self._normalize_key_name(raw_part)
            if normalized:
                key_set.add(normalized)
            else:
                logger.error(f"Unrecognized key '{raw_part}' in hotkey '{hotkey}'")

        if key_set:
            logger.info(f"Hotkey '{hotkey}' keys parsed: {key_set}")
        else:
            logger.error(f"Hotkey '{hotkey}' did not produce any valid keys")

    @staticmethod
    def _normalize_key_name(name: str) -> Optional[str]:
        """Normalize a key name from configuration or listener events."""

        if not name:
            return None

        name = name.lower().strip()

        # Handle single character keys (letters, numbers, punctuation)
        if len(name) == 1:
            if name == " ":
                return "space"
            if name == "\n":
                return "enter"
            if name == "\t":
                return "tab"

            # The caret key is typically produced by shift+6 on US layouts
            if name == "^":
                return "caret"

            return name

        alias_map = HotkeyService._get_alias_map()
        if name in alias_map:
            return alias_map[name]

        # Handle virtual key names such as 'ctrl_l'
        if name.endswith("_l") or name.endswith("_r"):
            base = name[:-2]
            if base in alias_map:
                return alias_map[base]

        # Replace spaces with underscores for matching
        normalized = name.replace(" ", "_")
        if normalized in alias_map:
            return alias_map[normalized]

        return normalized if normalized else None

    @staticmethod
    @functools.lru_cache(maxsize=1)
    def _get_alias_map() -> dict[str, str]:
        """
        Return mapping from alias name to canonical name.

        Loads from JSON configuration file and caches the result.
        """
        # Path to the hotkey aliases JSON file
        config_dir = Path(__file__).parent / "config"
        aliases_file = config_dir / "hotkey_aliases.json"

        try:
            with open(aliases_file, "r") as f:
                alias_groups = json.load(f)

            # Build lookup dictionary: each alias maps to its canonical name
            lookup: dict[str, str] = {}
            for canonical, aliases in alias_groups.items():
                for alias in aliases:
                    lookup[alias] = canonical
                # Also map canonical name to itself
                lookup[canonical] = canonical

            return lookup

        except FileNotFoundError:
            logger.error(f"Hotkey aliases file not found: {aliases_file}")
            # Return empty dict as fallback
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse hotkey aliases JSON: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading hotkey aliases: {e}")
            return {}

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

        # Stop listener if active
        listener = self._listener
        if listener:
            try:
                listener.stop()
            except Exception as exc:
                logger.debug(f"Error stopping hotkey listener: {exc}")

        # Wait for service thread to finish
        if self.service_thread and self.service_thread.is_alive():
            self.service_thread.join(timeout=5.0)
        self.service_thread = None

        with self._lock:
            self.current_keys.clear()
            self._push_hotkey_active = False
            self._toggle_hotkey_active = False

        logger.info("Hotkey service stopped")

    def _run_service(self):
        """Main service loop running in a separate thread."""
        listener: Optional[pynput_keyboard.Listener] = None

        try:
            while self.is_running:
                if listener is None or not listener.is_alive():
                    if listener is not None and self.is_running:
                        logger.warning(
                            "Hotkey listener stopped unexpectedly; attempting to restart."
                        )
                        try:
                            listener.stop()
                            listener.join(timeout=1.0)
                        except Exception:
                            pass

                    try:
                        listener = pynput_keyboard.Listener(
                            on_press=self._on_key_press,
                            on_release=self._on_key_release,
                        )
                        listener.start()
                        self._listener = listener
                        logger.debug("Hotkey listener thread started")
                    except Exception as exc:
                        listener = None
                        logger.error(f"Failed to start hotkey listener: {exc}")
                        time.sleep(1.0)
                        continue

                time.sleep(0.1)

        except Exception as e:
            logger.error(f"Error in hotkey service: {e}")
        finally:
            if listener is not None:
                try:
                    listener.stop()
                except Exception:
                    pass
                try:
                    listener.join(timeout=2.0)
                except Exception:
                    pass

            self._listener = None

            with self._lock:
                self.current_keys.clear()
                self._push_hotkey_active = False
                self._toggle_hotkey_active = False

    def _on_key_press(self, key):
        """Handle key press events from the global listener."""

        if not self.is_running:
            return

        key_name = self._key_to_name(key)
        if key_name is None:
            return

        with self._lock:
            self.current_keys.add(key_name)

            # Handle toggle hotkey first so toggle presses take precedence
            if self.toggle_hotkey_keys and self._are_keys_active(
                self.toggle_hotkey_keys
            ):
                if not self._toggle_hotkey_active:
                    self._toggle_hotkey_active = True
                    if self.is_recording:
                        self._stop_recording()
                    else:
                        self._start_recording(toggle_mode=True)
            else:
                self._toggle_hotkey_active = False

            # Handle push-to-talk hotkey
            if self.hotkey_keys and self._are_keys_active(self.hotkey_keys):
                self._push_hotkey_active = True
                if not self.is_recording:
                    self._start_recording(toggle_mode=False)

    def _on_key_release(self, key):
        """Handle key release events from the global listener."""

        if not self.is_running:
            return

        key_name = self._key_to_name(key)
        if key_name is None:
            return

        with self._lock:
            self.current_keys.discard(key_name)

            if self._toggle_hotkey_active and not self._are_keys_active(
                self.toggle_hotkey_keys
            ):
                self._toggle_hotkey_active = False

            if (
                self.is_recording
                and not self.is_toggle_mode
                and self._push_hotkey_active
                and not self._are_keys_active(self.hotkey_keys)
            ):
                self._push_hotkey_active = False
                self._stop_recording()
            elif not self._are_keys_active(self.hotkey_keys):
                self._push_hotkey_active = False

    def _key_to_name(self, key) -> Optional[str]:
        """Convert pynput key objects to normalized string names."""

        try:
            if isinstance(key, pynput_keyboard.Key):
                name = key.name
            elif isinstance(key, pynput_keyboard.KeyCode):
                if key.char:
                    name = key.char
                elif key.vk is not None:
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

            return self._normalize_key_name(str(name))

        except Exception as exc:
            logger.debug(f"Unable to normalize key '{key}': {exc}")
            return None

    def _are_keys_active(self, required_keys: Set[str]) -> bool:
        """Check if all keys in a combination are currently pressed."""

        if not required_keys:
            return False

        return all(key in self.current_keys for key in required_keys)

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
            if self.is_recording:
                mode_str = "toggle" if self.is_toggle_mode else "push-to-talk"
                self.is_recording = False
                self.is_toggle_mode = False
                logger.info(f"Recording stopped ({mode_str} mode)")

                if self.on_stop_recording:
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
            parsed_keys: Set[str] = set()
            self._parse_hotkey_combination(new_hotkey, parsed_keys)

            if not parsed_keys:
                raise ValueError("No valid keys in new hotkey")

            self.hotkey = new_hotkey
            self.hotkey_keys = parsed_keys

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
            parsed_keys: Set[str] = set()
            self._parse_hotkey_combination(new_toggle_hotkey, parsed_keys)

            if not parsed_keys:
                raise ValueError("No valid keys in new toggle hotkey")

            self.toggle_hotkey = new_toggle_hotkey
            self.toggle_hotkey_keys = parsed_keys

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
