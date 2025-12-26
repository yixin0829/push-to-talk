import sys
import types
from unittest.mock import MagicMock


from tests.test_helpers import create_keyboard_stub

# Setup keyboard stub for pynput imports
keyboard_stub = create_keyboard_stub()
sys.modules.setdefault("pynput", types.SimpleNamespace(keyboard=keyboard_stub))
sys.modules["pynput.keyboard"] = keyboard_stub

from src.hotkey_service import HotkeyService  # noqa: E402

# Aliases for backward compatibility in tests
pynput_keyboard = keyboard_stub
Key = keyboard_stub.Key


class TestHotkeyService:
    def setup_method(self):
        """Initialize a hotkey service instance for each test."""

        # Use explicit hotkeys for deterministic tests
        self.service = HotkeyService(
            hotkey="ctrl+shift+space", toggle_hotkey="ctrl+shift+t"
        )

    def teardown_method(self):
        """Ensure the service is stopped after each test."""

        if getattr(self.service, "is_running", False):
            self.service.stop_service()

    def test_initialization(self):
        """Verify that initialization populates expected defaults."""

        assert self.service.hotkey == "ctrl+shift+space"
        assert self.service.toggle_hotkey == "ctrl+shift+t"
        assert self.service.hotkey_keys == {"ctrl", "shift", "space"}
        assert self.service.toggle_hotkey_keys == {"ctrl", "shift", "t"}
        assert self.service.is_running is False
        assert self.service.is_recording is False
        assert self.service.is_toggle_mode is False
        assert self.service.service_thread is None

    def test_set_callbacks(self):
        """Callbacks should be stored for later invocation."""

        start_cb = MagicMock()
        stop_cb = MagicMock()
        self.service.set_callbacks(start_cb, stop_cb)

        assert self.service.on_start_recording is start_cb
        assert self.service.on_stop_recording is stop_cb

    def test_start_service_requires_callbacks(self):
        """Service should not start without configured callbacks."""

        assert self.service.start_service() is False
        assert self.service.is_running is False

    def test_start_service_success(self, mocker):
        """Starting the service should create and start a listener thread."""

        mock_thread = mocker.patch("src.hotkey_service.threading.Thread")
        start_cb = MagicMock()
        stop_cb = MagicMock()
        self.service.set_callbacks(start_cb, stop_cb)

        thread_instance = MagicMock()
        mock_thread.return_value = thread_instance

        assert self.service.start_service() is True
        assert self.service.is_running is True
        thread_instance.start.assert_called_once()

    def test_start_service_already_running(self):
        """Starting while running should be a no-op."""

        start_cb = MagicMock()
        stop_cb = MagicMock()
        self.service.set_callbacks(start_cb, stop_cb)

        self.service.is_running = True
        assert self.service.start_service() is False

    def test_start_service_thread_failure(self, mocker):
        """Thread creation failures should be surfaced as False."""

        mock_thread = mocker.patch(
            "src.hotkey_service.threading.Thread", side_effect=Exception("boom")
        )
        start_cb = MagicMock()
        stop_cb = MagicMock()
        self.service.set_callbacks(start_cb, stop_cb)

        assert self.service.start_service() is False
        assert self.service.is_running is False
        mock_thread.assert_called_once()

    def test_stop_service_when_not_running(self):
        """Stopping when idle should simply log and return."""

        self.service.stop_service()
        assert self.service.is_running is False

    def test_stop_service_cleans_state(self):
        """Stopping should terminate listener thread and clear key state."""

        self.service.is_running = True
        self.service.is_recording = True
        self.service.current_keys.update({"ctrl", "shift", "space"})
        self.service._listener = MagicMock()

        thread_mock = MagicMock()
        thread_mock.is_alive.return_value = True
        self.service.service_thread = thread_mock

        self.service.stop_service()

        self.service._listener.stop.assert_called_once()
        thread_mock.join.assert_called_once()
        assert self.service.current_keys == set()
        assert self.service.is_running is False
        assert self.service.is_recording is False

    def test_push_to_talk_flow(self):
        """Pressing and releasing the push-to-talk hotkey should start/stop recording."""

        start_cb = MagicMock()
        stop_cb = MagicMock()
        self.service.set_callbacks(start_cb, stop_cb)
        self.service.is_running = True

        self.service._on_key_press(pynput_keyboard.Key.ctrl)
        self.service._on_key_press(pynput_keyboard.Key.shift)
        self.service._on_key_press(pynput_keyboard.Key.space)

        assert self.service.is_recording is True
        assert self.service.is_toggle_mode is False
        start_cb.assert_called_once()

        self.service._on_key_release(pynput_keyboard.Key.space)
        self.service._on_key_release(pynput_keyboard.Key.shift)
        self.service._on_key_release(pynput_keyboard.Key.ctrl)

        assert self.service.is_recording is False
        stop_cb.assert_called_once()

    def test_toggle_hotkey_flow(self):
        """Toggle hotkey should start and stop recording on subsequent presses."""

        start_cb = MagicMock()
        stop_cb = MagicMock()
        self.service.set_callbacks(start_cb, stop_cb)
        self.service.is_running = True

        # First press starts toggle recording
        self.service._on_key_press(pynput_keyboard.Key.ctrl)
        self.service._on_key_press(pynput_keyboard.Key.shift)
        self.service._on_key_press(pynput_keyboard.KeyCode(char="t"))

        assert self.service.is_recording is True
        assert self.service.is_toggle_mode is True
        start_cb.assert_called_once()

        # Release without pressing again should keep recording
        self.service._on_key_release(pynput_keyboard.KeyCode(char="t"))
        self.service._on_key_release(pynput_keyboard.Key.shift)
        self.service._on_key_release(pynput_keyboard.Key.ctrl)

        assert self.service.is_recording is True
        assert self.service.is_toggle_mode is True

        # Second activation stops toggle mode
        self.service._on_key_press(pynput_keyboard.Key.ctrl)
        self.service._on_key_press(pynput_keyboard.Key.shift)
        self.service._on_key_press(pynput_keyboard.KeyCode(char="t"))

        assert self.service.is_recording is False
        assert self.service.is_toggle_mode is False
        stop_cb.assert_called_once()

    def test_change_hotkey_success(self):
        """Changing the push-to-talk hotkey should update internal state."""

        assert self.service.change_hotkey("ctrl+alt+r") is True
        assert self.service.hotkey == "ctrl+alt+r"
        assert self.service.hotkey_keys == {"ctrl", "alt", "r"}

    def test_change_hotkey_invalid(self):
        """Invalid hotkeys should be rejected."""

        assert self.service.change_hotkey("") is False
        assert self.service.hotkey == "ctrl+shift+space"

    def test_change_toggle_hotkey(self):
        """Toggle hotkey should be reconfigurable."""

        assert self.service.change_toggle_hotkey("ctrl+alt+y") is True
        assert self.service.toggle_hotkey == "ctrl+alt+y"
        assert self.service.toggle_hotkey_keys == {"ctrl", "alt", "y"}

    def test_change_toggle_hotkey_invalid(self):
        """Invalid toggle combinations should return False."""

        assert self.service.change_toggle_hotkey("") is False
        assert self.service.toggle_hotkey == "ctrl+shift+t"

    def test_key_normalization_handles_caret(self):
        """Caret key should normalize to a canonical representation."""

        service = HotkeyService(hotkey="ctrl+shift+space", toggle_hotkey="ctrl+shift+^")
        assert "caret" in service.toggle_hotkey_keys
        assert service._key_to_name(pynput_keyboard.KeyCode(char="^")) == "caret"

    def test_is_service_running_property(self):
        """Helper accessor should reflect running state."""

        assert self.service.is_service_running() is False
        self.service.is_running = True
        assert self.service.is_service_running() is True

    def test_get_recording_mode(self):
        """Recording mode helper should reflect toggle state."""

        assert self.service.get_recording_mode() == "idle"
        self.service.is_recording = True
        self.service.is_toggle_mode = False
        assert self.service.get_recording_mode() == "push-to-talk"
        self.service.is_toggle_mode = True
        assert self.service.get_recording_mode() == "toggle"


class TestHotkeyServicePlatformSupport:
    def test_macos_defaults(self, mocker):
        mocker.patch("sys.platform", "darwin")
        service = HotkeyService()
        assert service.hotkey == "cmd+shift+^"
        assert service.toggle_hotkey == "cmd+shift+space"
        assert HotkeyService.get_platform_name() == "macOS"
        assert HotkeyService.get_platform_modifier_key() == "cmd"

    def test_windows_defaults(self, mocker):
        mocker.patch("sys.platform", "win32")
        service = HotkeyService()
        assert service.hotkey == "ctrl+shift+^"
        assert service.toggle_hotkey == "ctrl+shift+space"
        assert HotkeyService.get_platform_name() == "Windows"
        assert HotkeyService.get_platform_modifier_key() == "ctrl"

    def test_linux_defaults(self, mocker):
        mocker.patch("sys.platform", "linux")
        service = HotkeyService()
        assert service.hotkey == "ctrl+shift+^"
        assert service.toggle_hotkey == "ctrl+shift+space"
        assert HotkeyService.get_platform_name() == "Linux"
        assert HotkeyService.get_platform_modifier_key() == "ctrl"

    def test_unknown_platform_defaults(self, mocker):
        mocker.patch("sys.platform", "freebsd")
        assert HotkeyService.get_platform_name() == "freebsd"


class TestHotkeyServiceKeyNormalization:
    def setup_method(self):
        """Initialize a hotkey service instance for each test."""
        self.service = HotkeyService(
            hotkey="ctrl+shift+space", toggle_hotkey="ctrl+shift+t"
        )

    def test_normalize_empty_key(self):
        """Empty key names should return None."""
        assert self.service._normalize_key_name("") is None
        assert self.service._normalize_key_name(None) is None

    def test_normalize_space_string(self):
        """'space' string should normalize through alias map."""
        result = self.service._normalize_key_name("space")
        assert result == "space"

    def test_normalize_enter_string(self):
        """'enter' string should normalize through alias map."""
        result = self.service._normalize_key_name("enter")
        assert result == "enter"

    def test_normalize_tab_string(self):
        """'tab' string should normalize through alias map."""
        result = self.service._normalize_key_name("tab")
        assert result == "tab"

    def test_normalize_single_letter(self):
        """Single letter should return itself."""
        assert self.service._normalize_key_name("a") == "a"
        assert self.service._normalize_key_name("z") == "z"
        assert self.service._normalize_key_name("5") == "5"

    def test_normalize_left_right_modifiers(self):
        """Left/right variants of modifiers should normalize to base form."""
        assert self.service._normalize_key_name("ctrl_l") == "ctrl"
        assert self.service._normalize_key_name("ctrl_r") == "ctrl"
        assert self.service._normalize_key_name("shift_l") == "shift"
        assert self.service._normalize_key_name("shift_r") == "shift"

    def test_normalize_with_spaces(self):
        """Key names with spaces should be normalized."""
        # Replace spaces with underscores for matching
        normalized = self.service._normalize_key_name("page down")
        assert normalized is not None

    def test_key_to_name_handles_key_object(self):
        """_key_to_name should handle pynput Key objects."""
        key = pynput_keyboard.Key.ctrl
        result = self.service._key_to_name(key)
        assert result == "ctrl"

    def test_key_to_name_handles_keycode_with_char(self):
        """_key_to_name should handle KeyCode with char."""
        key = pynput_keyboard.KeyCode(char="a")
        result = self.service._key_to_name(key)
        assert result == "a"

    def test_key_to_name_handles_keycode_with_vk(self):
        """_key_to_name should handle KeyCode with vk but no char."""
        key = pynput_keyboard.KeyCode(vk=65)  # Virtual key for 'a'
        result = self.service._key_to_name(key)
        assert result is not None

    def test_key_to_name_handles_keycode_with_no_char_or_vk(self):
        """_key_to_name should handle KeyCode with neither char nor vk."""
        key = pynput_keyboard.KeyCode()
        result = self.service._key_to_name(key)
        assert result is None

    def test_key_to_name_handles_unknown_key_type(self):
        """_key_to_name should handle unknown key types gracefully."""

        # Create a generic object with name attribute
        class UnknownKey:
            name = "unknown"

        key = UnknownKey()
        result = self.service._key_to_name(key)
        assert result == "unknown"

    def test_key_to_name_handles_exception(self):
        """_key_to_name should return None on exception."""

        class FailingKey:
            @property
            def name(self):
                raise RuntimeError("boom")

        key = FailingKey()
        result = self.service._key_to_name(key)
        assert result is None


class TestHotkeyServiceEdgeCases:
    def setup_method(self):
        """Initialize a hotkey service instance for each test."""
        self.service = HotkeyService(
            hotkey="ctrl+shift+space", toggle_hotkey="ctrl+shift+t"
        )

    def teardown_method(self):
        """Ensure the service is stopped after each test."""
        if getattr(self.service, "is_running", False):
            self.service.stop_service()

    def test_parse_hotkey_with_empty_parts(self):
        """Parsing hotkey with empty parts should handle gracefully."""
        key_set = set()
        self.service._parse_hotkey_combination("ctrl++shift", key_set)
        # Should still parse the valid keys
        assert "ctrl" in key_set
        assert "shift" in key_set

    def test_parse_hotkey_with_only_invalid_keys(self):
        """Parsing hotkey with only invalid keys should result in empty set."""
        key_set = set()
        # Empty hotkey
        self.service._parse_hotkey_combination("", key_set)
        assert len(key_set) == 0

    def test_are_keys_active_empty_required(self):
        """_are_keys_active should return False for empty required keys."""
        result = self.service._are_keys_active(set())
        assert result is False

    def test_stop_recording_when_not_recording(self):
        """_stop_recording should handle case when not recording."""
        self.service.is_recording = False
        # Should not raise
        self.service._stop_recording()
        assert self.service.is_recording is False

    def test_start_recording_callback_exception(self):
        """_start_recording should handle callback exceptions."""

        def failing_callback():
            raise RuntimeError("boom")

        self.service.on_start_recording = failing_callback
        self.service._start_recording()

        # Should have caught exception and reset state
        assert self.service.is_recording is False
        assert self.service.is_toggle_mode is False

    def test_stop_recording_callback_exception(self):
        """_stop_recording should handle callback exceptions."""

        def failing_callback():
            raise RuntimeError("boom")

        self.service.on_stop_recording = failing_callback
        self.service.is_recording = True

        # Should not raise
        self.service._stop_recording()

    def test_on_key_press_when_not_running(self):
        """_on_key_press should do nothing when service not running."""
        self.service.is_running = False
        # Should not raise or change state
        self.service._on_key_press(pynput_keyboard.Key.ctrl)
        assert len(self.service.current_keys) == 0

    def test_on_key_release_when_not_running(self):
        """_on_key_release should do nothing when service not running."""
        self.service.is_running = False
        self.service.current_keys.add("ctrl")
        # Should not remove key when not running
        self.service._on_key_release(pynput_keyboard.Key.ctrl)
        # Key was added before, should still be there since release was ignored
        assert "ctrl" in self.service.current_keys

    def test_on_key_press_with_none_key_name(self):
        """_on_key_press should handle keys that can't be normalized."""

        class WeirdKey:
            pass

        self.service.is_running = True
        # Should not raise
        self.service._on_key_press(WeirdKey())
        assert len(self.service.current_keys) == 0

    def test_on_key_release_with_none_key_name(self):
        """_on_key_release should handle keys that can't be normalized."""

        class WeirdKey:
            pass

        self.service.is_running = True
        self.service.current_keys.add("ctrl")
        # Should not raise or remove "ctrl"
        self.service._on_key_release(WeirdKey())
        assert "ctrl" in self.service.current_keys

    def test_get_hotkey_returns_current_hotkey(self):
        """get_hotkey should return current push-to-talk hotkey."""
        assert self.service.get_hotkey() == "ctrl+shift+space"

    def test_get_toggle_hotkey_returns_current_toggle_hotkey(self):
        """get_toggle_hotkey should return current toggle hotkey."""
        assert self.service.get_toggle_hotkey() == "ctrl+shift+t"

    def test_is_toggle_recording_when_not_recording(self):
        """is_toggle_recording should return False when not recording."""
        self.service.is_recording = False
        assert self.service.is_toggle_recording() is False

    def test_is_toggle_recording_in_push_to_talk_mode(self):
        """is_toggle_recording should return False when in push-to-talk mode."""
        self.service.is_recording = True
        self.service.is_toggle_mode = False
        assert self.service.is_toggle_recording() is False

    def test_is_toggle_recording_in_toggle_mode(self):
        """is_toggle_recording should return True when in toggle mode."""
        self.service.is_recording = True
        self.service.is_toggle_mode = True
        assert self.service.is_toggle_recording() is True

    def test_get_platform_default_hotkey(self):
        """get_platform_default_hotkey should return platform default."""
        result = HotkeyService.get_platform_default_hotkey()
        assert result is not None
        assert "+" in result

    def test_get_platform_default_toggle_hotkey(self):
        """get_platform_default_toggle_hotkey should return platform default."""
        result = HotkeyService.get_platform_default_toggle_hotkey()
        assert result is not None
        assert "+" in result

    def test_change_hotkey_while_running_restores_on_failure(self, mocker):
        """change_hotkey should restore service on parse failure."""
        start_cb = MagicMock()
        stop_cb = MagicMock()
        self.service.set_callbacks(start_cb, stop_cb)

        # Mock Thread to avoid actual threading
        mock_thread = mocker.patch("src.hotkey_service.threading.Thread")
        thread_instance = MagicMock()
        mock_thread.return_value = thread_instance

        self.service.start_service()
        original_hotkey = self.service.hotkey

        # Try to change to invalid hotkey
        result = self.service.change_hotkey("")

        assert result is False
        assert self.service.hotkey == original_hotkey
        # Service should have been restarted
        assert mock_thread.call_count >= 2

    def test_change_toggle_hotkey_while_running_restores_on_failure(self, mocker):
        """change_toggle_hotkey should restore service on parse failure."""
        start_cb = MagicMock()
        stop_cb = MagicMock()
        self.service.set_callbacks(start_cb, stop_cb)

        # Mock Thread to avoid actual threading
        mock_thread = mocker.patch("src.hotkey_service.threading.Thread")
        thread_instance = MagicMock()
        mock_thread.return_value = thread_instance

        self.service.start_service()
        original_toggle_hotkey = self.service.toggle_hotkey

        # Try to change to invalid hotkey
        result = self.service.change_toggle_hotkey("")

        assert result is False
        assert self.service.toggle_hotkey == original_toggle_hotkey
        # Service should have been restarted
        assert mock_thread.call_count >= 2

    def test_stop_service_stops_ongoing_recording(self):
        """stop_service should stop any ongoing recording."""
        start_cb = MagicMock()
        stop_cb = MagicMock()
        self.service.set_callbacks(start_cb, stop_cb)

        self.service.is_running = True
        self.service.is_recording = True
        self.service._listener = MagicMock()
        self.service.service_thread = MagicMock()
        self.service.service_thread.is_alive.return_value = False

        self.service.stop_service()

        assert self.service.is_recording is False
        stop_cb.assert_called_once()

    def test_stop_service_handles_listener_stop_exception(self):
        """stop_service should handle exceptions when stopping listener."""
        self.service.is_running = True
        mock_listener = MagicMock()
        mock_listener.stop.side_effect = RuntimeError("boom")
        self.service._listener = mock_listener
        self.service.service_thread = MagicMock()
        self.service.service_thread.is_alive.return_value = False

        # Should not raise
        self.service.stop_service()

        assert self.service.is_running is False
