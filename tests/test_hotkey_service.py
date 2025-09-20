import sys
import types
from typing import Optional
from unittest.mock import MagicMock, patch


class DummyKey:
    def __init__(self, name: Optional[str] = None):
        if name is not None:
            self.name = name


class DummyKeyCode:
    def __init__(self, char: Optional[str] = None, vk: Optional[int] = None):
        self.char = char
        self.vk = vk

    @classmethod
    def from_vk(cls, vk: int):
        return cls(vk=vk)


class DummyListener:
    def __init__(self, on_press=None, on_release=None):
        self.on_press = on_press
        self.on_release = on_release
        self._alive = False

    def start(self):  # pragma: no cover - trivial
        self._alive = True

    def stop(self):  # pragma: no cover - trivial
        self._alive = False

    def join(self, timeout=None):  # pragma: no cover - trivial
        return None

    def is_alive(self):  # pragma: no cover - trivial
        return self._alive


# Populate common key objects used by the service
Key = DummyKey
Key.ctrl = DummyKey("ctrl")
Key.shift = DummyKey("shift")
Key.space = DummyKey("space")
Key.alt = DummyKey("alt")
Key.cmd = DummyKey("cmd")
Key.ctrl_l = DummyKey("ctrl_l")
Key.ctrl_r = DummyKey("ctrl_r")
Key.shift_l = DummyKey("shift_l")
Key.shift_r = DummyKey("shift_r")
Key.cmd_l = DummyKey("cmd_l")
Key.cmd_r = DummyKey("cmd_r")

keyboard_stub = types.SimpleNamespace(
    Listener=DummyListener,
    Key=Key,
    KeyCode=DummyKeyCode,
)

sys.modules.setdefault("pynput", types.SimpleNamespace(keyboard=keyboard_stub))
sys.modules["pynput.keyboard"] = keyboard_stub

from src.hotkey_service import HotkeyService  # noqa: E402

pynput_keyboard = keyboard_stub


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

    @patch("src.hotkey_service.threading.Thread")
    def test_start_service_success(self, mock_thread):
        """Starting the service should create and start a listener thread."""

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

    @patch("src.hotkey_service.threading.Thread", side_effect=Exception("boom"))
    def test_start_service_thread_failure(self, mock_thread):
        """Thread creation failures should be surfaced as False."""

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
    @patch("sys.platform", "darwin")
    def test_macos_defaults(self):
        service = HotkeyService()
        assert service.hotkey == "cmd+shift+space"
        assert service.toggle_hotkey == "cmd+shift+^"
        assert HotkeyService.get_platform_name() == "macOS"
        assert HotkeyService.get_platform_modifier_key() == "cmd"

    @patch("sys.platform", "win32")
    def test_windows_defaults(self):
        service = HotkeyService()
        assert service.hotkey == "ctrl+shift+space"
        assert service.toggle_hotkey == "ctrl+shift+^"
        assert HotkeyService.get_platform_name() == "Windows"
        assert HotkeyService.get_platform_modifier_key() == "ctrl"

    @patch("sys.platform", "linux")
    def test_linux_defaults(self):
        service = HotkeyService()
        assert service.hotkey == "ctrl+shift+space"
        assert service.toggle_hotkey == "ctrl+shift+^"
        assert HotkeyService.get_platform_name() == "Linux"
        assert HotkeyService.get_platform_modifier_key() == "ctrl"
